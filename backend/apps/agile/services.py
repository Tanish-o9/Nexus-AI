"""
Agile services: analytics, velocity, burndown, reports, exports.
"""

import csv
import io
from collections import defaultdict
from datetime import date, timedelta

from django.db.models import Count, Sum, Q
from django.utils import timezone

from apps.projects.models import Task
from .models import Sprint, SprintBacklogItem, SprintReport


# ── Analytics ──────────────────────────────────────────────────────────────────

def get_project_analytics(project_id: str) -> dict:
    """Aggregate project analytics."""
    tasks = Task.objects.filter(project_id=project_id)
    total = tasks.count()
    if total == 0:
        return {
            'totalTasks': 0, 'completedTasks': 0, 'inProgressTasks': 0,
            'todoTasks': 0, 'completionRate': 0,
            'byPriority': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
            'byAssignee': [], 'overdueTasks': 0,
        }

    completed = tasks.filter(status='done').count()
    in_progress = tasks.filter(status='in_progress').count()
    todo = tasks.filter(status='todo').count()
    overdue = tasks.filter(
        Q(due_date__lt=date.today()) & ~Q(status='done')
    ).count()

    # By priority
    by_priority = {
        'critical': tasks.filter(priority='critical').count(),
        'high': tasks.filter(priority='high').count(),
        'medium': tasks.filter(priority='medium').count(),
        'low': tasks.filter(priority='low').count(),
    }

    # By assignee
    by_assignee = list(
        tasks.values('assignee__username').annotate(
            count=Count('id'),
            completed=Count('id', filter=Q(status='done')),
        ).filter(assignee__username__isnull=False)
    )

    return {
        'totalTasks': total,
        'completedTasks': completed,
        'inProgressTasks': in_progress,
        'todoTasks': todo,
        'completionRate': round((completed / total) * 100, 2),
        'byPriority': by_priority,
        'byAssignee': by_assignee,
        'overdueTasks': overdue,
    }


# ── Velocity ───────────────────────────────────────────────────────────────────

def get_velocity(project_id: str, sprint_count: int = 5) -> dict:
    """Calculate team velocity from completed sprints."""
    sprints = Sprint.objects.filter(
        project_id=project_id, is_completed=True
    ).prefetch_related('backlog_items__task')[:sprint_count]

    if not sprints:
        return {'averageVelocity': 0, 'sprints': []}

    data = []
    for sprint in sprints:
        total_points = sum(bi.story_points for bi in sprint.backlog_items.all())
        completed_points = sum(
            bi.story_points for bi in sprint.backlog_items.select_related('task').all()
            if bi.task.status == 'done'
        )
        data.append({
            'sprintId': str(sprint.id),
            'sprintName': sprint.name,
            'totalPoints': total_points,
            'completedPoints': completed_points,
        })

    avg = sum(d['completedPoints'] for d in data) / len(data) if data else 0
    return {'averageVelocity': round(avg, 2), 'sprints': data}


# ── Burndown ───────────────────────────────────────────────────────────────────

def get_burndown(sprint_id: str) -> dict:
    """Generate burndown chart data for a sprint."""
    try:
        sprint = Sprint.objects.get(pk=sprint_id)
    except Sprint.DoesNotExist:
        return {'labels': [], 'ideal': [], 'actual': [], 'totalPoints': 0}

    items = list(sprint.backlog_items.select_related('task').all())
    if not items:
        return {'labels': [], 'ideal': [], 'actual': [], 'totalPoints': 0}

    total_points = sum(i.story_points for i in items)
    days = (sprint.end_date - sprint.start_date).days or 1
    daily_burn = total_points / days

    # Build day-by-day burndown
    labels = []
    ideal = []
    actual = []
    remaining = total_points

    for day_offset in range(days + 1):
        current_date = sprint.start_date + timedelta(days=day_offset)
        labels.append(current_date.isoformat())
        ideal.append(round(total_points - (daily_burn * day_offset), 2))

        # Count tasks completed up to this date
        completed_up_to = sum(
            i.story_points for i in items
            if i.task.status == 'done' and (
                i.task.updated_at.date() <= current_date
            )
        )
        actual.append(round(total_points - completed_up_to, 2))

    return {
        'labels': labels,
        'ideal': ideal,
        'actual': actual,
        'totalPoints': total_points,
    }


# ── Workload ───────────────────────────────────────────────────────────────────

def get_workload(project_id: str) -> list[dict]:
    """Calculate workload distribution per assignee."""
    tasks = Task.objects.filter(project_id=project_id).exclude(assignee__isnull=True)
    assignee_data = defaultdict(lambda: {'active': 0, 'completed': 0, 'overdue': 0, 'totalPoints': 0})

    for task in tasks.select_related('assignee').prefetch_related('sprint_assignments'):
        username = task.assignee.username
        assignee_data[username]['active'] += 1 if task.status not in ('done',) else 0
        assignee_data[username]['completed'] += 1 if task.status == 'done' else 0
        assignee_data[username]['overdue'] += 1 if (
            task.due_date and task.due_date < date.today() and task.status != 'done'
        ) else 0
        points = task.sprint_assignments.first()
        if points:
            assignee_data[username]['totalPoints'] += points.story_points

    return [
        {
            'assignee': name,
            'activeTasks': d['active'],
            'completedTasks': d['completed'],
            'overdueTasks': d['overdue'],
            'totalPoints': round(d['totalPoints'], 1),
        }
        for name, d in sorted(assignee_data.items())
    ]


# ── Deadline Risk ──────────────────────────────────────────────────────────────

def get_deadline_risk(project_id: str) -> list[dict]:
    """Identify tasks at risk of missing deadlines."""
    today = date.today()
    risky = Task.objects.filter(
        project_id=project_id,
        due_date__isnull=False,
    ).exclude(status='done').select_related('assignee')

    results = []
    for task in risky:
        days_remaining = (task.due_date - today).days
        risk = 'overdue' if days_remaining < 0 else (
            'high' if days_remaining <= 2 else (
                'medium' if days_remaining <= 7 else 'low'
            )
        )
        results.append({
            'taskId': str(task.id),
            'title': task.title,
            'assignee': task.assignee.username if task.assignee else '',
            'dueDate': task.due_date.isoformat(),
            'daysRemaining': days_remaining,
            'riskLevel': risk,
            'status': task.status,
        })

    return sorted(results, key=lambda r: r['daysRemaining'])


# ── Reports ────────────────────────────────────────────────────────────────────

def generate_sprint_report(sprint_id: str, report_type: str = 'sprint') -> SprintReport:
    """Generate a structured sprint report."""
    sprint = Sprint.objects.get(pk=sprint_id)
    analytics = get_project_analytics(str(sprint.project_id))
    velocity = get_velocity(str(sprint.project_id))
    workload = get_workload(str(sprint.project_id))
    burndown = get_burndown(sprint_id)
    risks = get_deadline_risk(str(sprint.project_id))

    data = {
        'sprintName': sprint.name,
        'goal': sprint.goal,
        'startDate': sprint.start_date.isoformat(),
        'endDate': sprint.end_date.isoformat(),
        'analytics': analytics,
        'velocity': velocity,
        'workload': workload,
        'burndown': burndown,
        'deadlineRisks': risks[:10],
    }

    return SprintReport.objects.create(
        sprint=sprint,
        report_type=report_type,
        data=data,
    )


# ── Export ─────────────────────────────────────────────────────────────────────

def export_report_csv(report_id: str) -> str:
    """Generate CSV export of a report."""
    report = SprintReport.objects.get(pk=report_id)
    data = report.data
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['Sprint Report', data.get('sprintName', '')])
    writer.writerow(['Goal', data.get('goal', '')])
    writer.writerow(['Period', f'{data.get("startDate", "")} → {data.get("endDate", "")}'])
    writer.writerow([])

    analytics = data.get('analytics', {})
    writer.writerow(['Analytics'])
    writer.writerow(['Total Tasks', analytics.get('totalTasks', 0)])
    writer.writerow(['Completed', analytics.get('completedTasks', 0)])
    writer.writerow(['Completion Rate', f'{analytics.get("completionRate", 0)}%'])
    writer.writerow(['Overdue', analytics.get('overdueTasks', 0)])
    writer.writerow([])

    risks = data.get('deadlineRisks', [])
    if risks:
        writer.writerow(['Deadline Risks'])
        writer.writerow(['Task', 'Assignee', 'Due Date', 'Risk Level'])
        for r in risks:
            writer.writerow([r['title'], r['assignee'], r['dueDate'], r['riskLevel']])

    return output.getvalue()


def export_report_excel(report_id: str) -> bytes:
    """Generate Excel export via simple XLSX structure (placeholder)."""
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sprint Report'

    report = SprintReport.objects.get(pk=report_id)
    data = report.data

    ws.append(['Sprint Report', data.get('sprintName', '')])
    ws.append(['Goal', data.get('goal', '')])
    ws.append([])

    analytics = data.get('analytics', {})
    ws.append(['Analytics'])
    ws.append(['Total Tasks', analytics.get('totalTasks', 0)])
    ws.append(['Completed', analytics.get('completedTasks', 0)])
    ws.append(['Completion Rate', f'{analytics.get("completionRate", 0)}%'])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.read()