"""
AI Module Service
=================
Implements all AI module features using LangChain, LangGraph, and existing
RAG infrastructure.

Features:
  1. AI Chat        — Conversational AI with session history
  2. Task Breakdown — Decompose complex tasks into subtasks
  3. Sprint Planning— Plan a sprint from backlog items
  4. Project Summary— Generate a project status summary
  5. Doc Q&A (RAG)  — Question answering over ingested documents
  6. Meeting Summary— Summarise meeting notes into structured output
  7. PR Review      — Review GitHub pull requests
  8. Bug Explanation— Analyse and explain bugs
  9. Deadline Prediction — Predict task completion dates
  10. Risk Analysis — Identify and assess project risks
  11. Workload Suggestion — Suggest optimal task assignments
  12. Daily Standup Summary — Summarize daily standup updates
  13. Weekly Project Summary — Generate weekly project reports
  14. Release Notes Generator — Generate release notes from commits
  15. Smart Task Assignment — AI-powered task assignment recommendations
  16. Duplicate Task Detection — Detect duplicate or similar tasks
  17. Project Health Score — Calculate comprehensive project health metrics
"""

from __future__ import annotations

import json
import logging
from datetime import date
from typing import Any

from app.config import get_settings
from app.prompts.ai_module import get_ai_prompt
from app.schemas.ai_module import (
    AIContext,
    # Chat
    # (uses existing ChatRequest/ChatResponse)
    # Task Breakdown
    TaskBreakdownRequest,
    TaskBreakdownResponse,
    TaskBreakdownItem,
    # Sprint Planning
    SprintPlanningRequest,
    SprintPlanningResponse,
    SprintGoal,
    # Project Summary
    ProjectSummaryRequest,
    ProjectSummaryResponse,
    # Doc QA
    DocQARequest,
    DocQAResponse,
    # Meeting Summary
    MeetingSummaryRequest,
    MeetingSummaryResponse,
    ActionItem,
    # PR Review
    PRReviewRequest,
    PRReviewResponse,
    # Bug Explanation
    BugExplanationRequest,
    BugExplanationResponse,
    # Deadline Prediction
    DeadlinePredictionRequest,
    DeadlinePredictionResponse,
    TaskDeadlinePrediction,
    # Risk Analysis
    RiskAnalysisRequest,
    RiskAnalysisResponse,
    RiskItem,
    # Workload Suggestion
    WorkloadSuggestionRequest,
    WorkloadSuggestionResponse,
    WorkloadAssignment,
    # Standup Summary
    StandupSummaryRequest,
    StandupSummaryResponse,
    # Weekly Summary
    WeeklySummaryRequest,
    WeeklySummaryResponse,
    # Release Notes
    ReleaseNotesRequest,
    ReleaseNotesResponse,
    # Smart Task Assignment
    SmartTaskAssignmentRequest,
    SmartTaskAssignmentResponse,
    # Duplicate Task Detection
    DuplicateTaskDetectionRequest,
    DuplicateTaskResponse,
    # Project Health Score
    ProjectHealthScoreRequest,
    ProjectHealthScoreResponse,
)
from app.services.llm import get_sync_llm
from app.services.embeddings import embed_text
from app.services.hybrid_search import hybrid_search_chunks
from app.services.re_ranker import rerank
from app.services.citations import format_citations_for_prompt
from app.memory.database import AsyncSessionFactory
from app.tools.registry import tool_registry
from app.tools.schemas import ToolContext

logger = logging.getLogger(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _fetch_project_data(context: AIContext) -> str:
    """Fetch project overview data using the existing tool infrastructure."""
    try:
        from app.tools.project_data import get_project_overview
        from app.tools.schemas import ProjectOverviewInput

        tool_ctx = ToolContext(
            user_id=context.user_id,
            org_id=context.org_id,
            project_id=context.project_id,
        )
        result = await get_project_overview(ProjectOverviewInput(), tool_ctx)
        if result.ok and result.data:
            return json.dumps(result.data, indent=2)
        return "Project data unavailable."
    except Exception:
        logger.warning("Failed to fetch project data", exc_info=True)
        return "Project data unavailable."


def _parse_json_response(raw: str) -> dict[str, Any]:
    """Parse JSON from LLM response, stripping markdown fences if present."""
    text = raw.strip()
    # Remove markdown code fences if present
    if text.startswith("```"):
        # Find the first { or [ after the fence
        start = text.find("{") if "{" in text else text.find("[")
        if start == -1:
            raise ValueError("No JSON content found in LLM response")
        text = text[start:]
        # Remove trailing fence
        end = text.rfind("}")
        if end != -1:
            text = text[: end + 1]
        elif text.rfind("]") != -1:
            end = text.rfind("]")
            text = text[: end + 1]
    return json.loads(text)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. AI Chat
# ═══════════════════════════════════════════════════════════════════════════════

async def ai_chat(
    message: str,
    context: AIContext,
    history: list[dict[str, str]] | None = None,
) -> str:
    """
    General-purpose AI chat with project context awareness.
    Uses the existing LangChain streaming infrastructure under the hood.
    """
    settings = get_settings()
    prompt = get_ai_prompt("ai_chat_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Convert history dicts to LangChain messages
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

    lc_history = []
    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                lc_history.append(HumanMessage(content=content))
            elif role == "assistant":
                lc_history.append(AIMessage(content=content))
            elif role == "system":
                lc_history.append(SystemMessage(content=content))

    result = await chain.ainvoke({
        "message": message,
        "history": lc_history,
        "org_id": context.org_id or "N/A",
        "project_id": context.project_id or "N/A",
    })

    return result.content if hasattr(result, "content") else str(result)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Task Breakdown
# ═══════════════════════════════════════════════════════════════════════════════

async def task_breakdown(request: TaskBreakdownRequest) -> TaskBreakdownResponse:
    """Break a complex task into structured subtasks."""
    prompt = get_ai_prompt("task_breakdown_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    result = await chain.ainvoke({"task_description": request.task_description})
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    subtasks = []
    for item in data.get("subtasks", []):
        subtasks.append(TaskBreakdownItem(
            title=item.get("title", "Untitled"),
            description=item.get("description", ""),
            estimated_hours=item.get("estimated_hours"),
            dependencies=item.get("dependencies", []),
            priority=item.get("priority", "medium"),
            assignee_suggestion=item.get("assignee_suggestion"),
        ))

    return TaskBreakdownResponse(
        task_summary=data.get("task_summary", ""),
        subtasks=subtasks,
        total_estimated_hours=data.get("total_estimated_hours"),
        notes=data.get("notes", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Sprint Planning
# ═══════════════════════════════════════════════════════════════════════════════

async def sprint_planning(request: SprintPlanningRequest) -> SprintPlanningResponse:
    """Plan a sprint from backlog items."""
    prompt = get_ai_prompt("sprint_planning_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    backlog_text = ", ".join(request.backlog_items) if request.backlog_items else "No specific backlog items provided"
    focus_area = request.focus_area or "General"

    result = await chain.ainvoke({
        "sprint_duration_days": request.sprint_duration_days,
        "backlog_items": backlog_text,
        "team_capacity_hours": request.team_capacity_hours or "Unknown",
        "focus_area": focus_area,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    sprint_goals = []
    for goal in data.get("sprint_goals", []):
        sprint_goals.append(SprintGoal(
            title=goal.get("title", "Untitled"),
            description=goal.get("description", ""),
            tasks=goal.get("tasks", []),
        ))

    return SprintPlanningResponse(
        sprint_goals=sprint_goals,
        recommended_velocity=data.get("recommended_velocity", ""),
        risk_factors=data.get("risk_factors", []),
        capacity_utilization=data.get("capacity_utilization", ""),
        notes=data.get("notes", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Project Summary
# ═══════════════════════════════════════════════════════════════════════════════

async def project_summary(request: ProjectSummaryRequest) -> ProjectSummaryResponse:
    """Generate a comprehensive project summary."""
    prompt = get_ai_prompt("project_summary_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    project_data = await _fetch_project_data(request.context)

    focus_areas_text = ", ".join(request.focus_areas) if request.focus_areas else "All areas"

    result = await chain.ainvoke({
        "focus_areas": focus_areas_text,
        "project_data": project_data,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return ProjectSummaryResponse(
        overview=data.get("overview", ""),
        status=data.get("status", "unknown"),
        recent_activity=data.get("recent_activity", ""),
        open_risks=data.get("open_risks", []),
        next_milestones=data.get("next_milestones", []),
        health_metrics=data.get("health_metrics", {}),
        summary=data.get("summary", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Documentation Q&A (RAG)
# ═══════════════════════════════════════════════════════════════════════════════

async def doc_qa(request: DocQARequest) -> DocQAResponse:
    """Answer questions over ingested documents using RAG."""
    if not request.context.org_id:
        return DocQAResponse(
            answer="Organization ID is required for document search.",
            sources=[],
            confidence="low",
            follow_up_questions=[],
        )

    # Step 1: Hybrid search for relevant chunks
    async with AsyncSessionFactory() as session:
        results = await hybrid_search_chunks(
            session,
            query=request.question,
            org_id=request.context.org_id,
            project_id=request.context.project_id,
            top_k=request.top_k * 2,  # Get more for re-ranker
        )

        # Step 2: Optional re-ranking
        if request.use_reranker and results:
            results = await rerank(request.question, results, top_k=request.top_k)

    if not results:
        return DocQAResponse(
            answer="No relevant documents found to answer your question.",
            sources=[],
            confidence="low",
            follow_up_questions=["Try rephrasing your question", "Upload more relevant documents"],
        )

    # Step 3: Format context for the LLM
    retrieved_context = format_citations_for_prompt(results)

    # Step 4: Generate answer using LLM with retrieved context
    prompt = get_ai_prompt("doc_qa_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    result = await chain.ainvoke({
        "retrieved_context": retrieved_context,
        "question": request.question,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    sources = data.get("sources", [])
    # If LLM didn't return sources, build them from search results
    if not sources:
        sources = []
        for i, r in enumerate(results[:3]):
            sources.append({
                "id": f"src_{i + 1}",
                "title": r.metadata.get("source", "unknown"),
                "excerpt": r.content[:200],
            })

    return DocQAResponse(
        answer=data.get("answer", ""),
        sources=sources,
        confidence=data.get("confidence", "medium"),
        follow_up_questions=data.get("follow_up_questions", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Meeting Summary
# ═══════════════════════════════════════════════════════════════════════════════

async def meeting_summary(request: MeetingSummaryRequest) -> MeetingSummaryResponse:
    """Summarise meeting notes into a structured format."""
    prompt = get_ai_prompt("meeting_summary_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    result = await chain.ainvoke({
        "meeting_type": request.meeting_type,
        "meeting_notes": request.meeting_notes,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    action_items = []
    for item in data.get("action_items", []):
        action_items.append(ActionItem(
            owner=item.get("owner", "Unassigned"),
            task=item.get("task", ""),
            deadline=item.get("deadline"),
        ))

    # Parse date string
    summary_date = date.today()
    date_str = data.get("date")
    if date_str and isinstance(date_str, str):
        try:
            summary_date = date.fromisoformat(date_str)
        except ValueError:
            pass

    return MeetingSummaryResponse(
        title=data.get("title", "Meeting Summary"),
        date=summary_date,
        attendees_summary=data.get("attendees_summary", ""),
        key_discussion_points=data.get("key_discussion_points", []),
        decisions=data.get("decisions", []),
        action_items=action_items,
        next_steps=data.get("next_steps", []),
        full_summary=data.get("full_summary", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. PR Review
# ═══════════════════════════════════════════════════════════════════════════════

async def pr_review(request: PRReviewRequest) -> PRReviewResponse:
    """Review a GitHub pull request."""
    # Fetch PR data from GitHub using existing tool infrastructure
    from app.tools.github import search_github_issues
    from app.tools.schemas import GitHubIssuesInput

    tool_ctx = ToolContext(
        user_id=request.context.user_id,
        org_id=request.context.org_id,
        project_id=request.context.project_id,
    )

    # Get PR details via GitHub issues tool
    # (PRs are issues with pull_request metadata)
    pr_data = f"PR #{request.pr_number} in {request.repository}"

    # Try to fetch PR data
    try:
        result = await search_github_issues(
            GitHubIssuesInput(
                repository=request.repository,
                query=f"is:pr {request.pr_number}",
                state="all",
                limit=1,
            ),
            tool_ctx,
        )
        if result.ok and result.data:
            pr_data = json.dumps(result.data, indent=2)
    except Exception:
        logger.warning(f"Could not fetch PR #{request.pr_number} data from GitHub")
        pr_data = f"PR #{request.pr_number} in {request.repository}\n(GitHub fetch failed, analysing based on PR number only)"

    prompt = get_ai_prompt("pr_review_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    focus_text = ", ".join(request.review_focus) if request.review_focus else "general code quality"

    result = await chain.ainvoke({
        "focus_areas": focus_text,
        "pr_number": request.pr_number,
        "repository": request.repository,
        "pr_data": pr_data,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return PRReviewResponse(
        summary=data.get("summary", ""),
        code_quality_issues=data.get("code_quality_issues", []),
        security_concerns=data.get("security_concerns", []),
        performance_notes=data.get("performance_notes", []),
        suggested_improvements=data.get("suggested_improvements", []),
        overall_assessment=data.get("overall_assessment", "needs_discussion"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Bug Explanation
# ═══════════════════════════════════════════════════════════════════════════════

async def bug_explanation(request: BugExplanationRequest) -> BugExplanationResponse:
    """Analyse and explain a bug."""
    prompt = get_ai_prompt("bug_explanation_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Build the bug input from available data
    bug_parts = []
    if request.behavior_description:
        bug_parts.append(f"Expected vs Actual: {request.behavior_description}")
    if request.error_message:
        bug_parts.append(f"Error: {request.error_message}")
    if request.code_snippet:
        bug_parts.append(f"Code:\n```{request.language}\n{request.code_snippet}\n```")
    bug_input = "\n\n".join(bug_parts) if bug_parts else "No specific details provided."

    result = await chain.ainvoke({
        "language": request.language,
        "bug_input": bug_input,
        "project_context": request.project_context or "No additional context.",
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return BugExplanationResponse(
        root_cause=data.get("root_cause", ""),
        explanation=data.get("explanation", ""),
        suggested_fix=data.get("suggested_fix", ""),
        severity=data.get("severity", "medium"),
        related_files=data.get("related_files", []),
        prevention_tips=data.get("prevention_tips", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Deadline Prediction
# ═══════════════════════════════════════════════════════════════════════════════

async def deadline_prediction(request: DeadlinePredictionRequest) -> DeadlinePredictionResponse:
    """Predict completion dates for tasks."""
    prompt = get_ai_prompt("deadline_prediction_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Fetch project data for richer context
    project_data = await _fetch_project_data(request.context)

    task_data = project_data if project_data != "Project data unavailable." else "No specific task data available."
    assumptions_text = ", ".join(request.assumptions) if request.assumptions else "Standard velocity estimates"

    result = await chain.ainvoke({
        "task_data": task_data,
        "assumptions": assumptions_text,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    predictions = []
    for pred in data.get("predictions", []):
        pred_date = date.today()
        date_str = pred.get("predicted_completion_date")
        if date_str and isinstance(date_str, str):
            try:
                pred_date = date.fromisoformat(date_str)
            except ValueError:
                pass

        predictions.append(TaskDeadlinePrediction(
            task_id=pred.get("task_id", "unknown"),
            task_title=pred.get("task_title", "Untitled"),
            predicted_completion_date=pred_date,
            confidence=pred.get("confidence", "medium"),
            risk_factors=pred.get("risk_factors", []),
        ))

    return DeadlinePredictionResponse(
        predictions=predictions,
        overall_risk=data.get("overall_risk", "on_track"),
        methodology=data.get("methodology", "AI-powered estimation based on project context"),
        notes=data.get("notes", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Risk Analysis
# ═══════════════════════════════════════════════════════════════════════════════

async def risk_analysis(request: RiskAnalysisRequest) -> RiskAnalysisResponse:
    """Analyse project risks."""
    prompt = get_ai_prompt("risk_analysis_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    project_data = await _fetch_project_data(request.context)
    focus_text = ", ".join(request.focus_areas) if request.focus_areas else "All areas"

    result = await chain.ainvoke({
        "project_data": project_data,
        "focus_areas": focus_text,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    risks = []
    for item in data.get("risks", []):
        risks.append(RiskItem(
            risk=item.get("risk", ""),
            probability=item.get("probability", "medium"),
            impact=item.get("impact", "medium"),
            mitigation=item.get("mitigation", ""),
            owner=item.get("owner", ""),
        ))

    return RiskAnalysisResponse(
        summary=data.get("summary", ""),
        risks=risks,
        top_priority=data.get("top_priority", ""),
        overall_health=data.get("overall_health", "healthy"),
        recommendations=data.get("recommendations", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 11. Workload Suggestion
# ═══════════════════════════════════════════════════════════════════════════════

async def workload_suggestion(request: WorkloadSuggestionRequest) -> WorkloadSuggestionResponse:
    """Suggest optimal task distribution across team members."""
    prompt = get_ai_prompt("workload_suggestion_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Build team data string
    team_lines = []
    for member in request.team_members:
        skills_str = ", ".join(member.skills) if member.skills else "General"
        team_lines.append(f"- {member.name}: {member.current_load}% load, skills: [{skills_str}]")
    team_data = "\n".join(team_lines)

    tasks_text = "\n".join(f"- {t}" for t in request.upcoming_tasks) if request.upcoming_tasks else "No specific tasks provided"

    result = await chain.ainvoke({
        "team_data": team_data,
        "upcoming_tasks": tasks_text,
        "balance_factor": request.balance_factor,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    assignments = []
    for item in data.get("assignments", []):
        assignments.append(WorkloadAssignment(
            task=item.get("task", ""),
            assignee=item.get("assignee", "Unassigned"),
            rationale=item.get("rationale", ""),
            estimated_hours=item.get("estimated_hours"),
        ))

    return WorkloadSuggestionResponse(
        assignments=assignments,
        team_utilization=data.get("team_utilization", {}),
        recommendations=data.get("recommendations", []),
        summary=data.get("summary", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 12. Daily Standup Summary
# ═══════════════════════════════════════════════════════════════════════════════

async def standup_summary(request: StandupSummaryRequest) -> StandupSummaryResponse:
    """Generate a daily standup summary from team updates."""
    prompt = get_ai_prompt("standup_summary_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    updates_text = "\n\n".join(f"Update {i+1}:\n{update}" for i, update in enumerate(request.team_updates))

    result = await chain.ainvoke({
        "team_updates": updates_text,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    action_items = []
    for item in data.get("action_items", []):
        action_items.append(ActionItem(
            owner=item.get("owner", "Unassigned"),
            task=item.get("task", ""),
            deadline=item.get("deadline"),
        ))

    return StandupSummaryResponse(
        summary=data.get("summary", ""),
        blockers=data.get("blockers", []),
        action_items=action_items,
        team_morale=data.get("team_morale", "neutral"),
        sprint_health=data.get("sprint_health", "on_track"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 13. Weekly Project Summary
# ═══════════════════════════════════════════════════════════════════════════════

async def weekly_summary(request: WeeklySummaryRequest) -> WeeklySummaryResponse:
    """Generate a weekly project summary."""
    prompt = get_ai_prompt("weekly_summary_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    project_data = await _fetch_project_data(request.context)

    result = await chain.ainvoke({
        "week_start_date": request.week_start_date,
        "project_data": project_data,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return WeeklySummaryResponse(
        week_summary=data.get("week_summary", ""),
        key_achievements=data.get("key_achievements", []),
        challenges_faced=data.get("challenges_faced", []),
        metrics=data.get("metrics", {}),
        next_week_priorities=data.get("next_week_priorities", []),
        overall_sentiment=data.get("overall_sentiment", "neutral"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 14. Release Notes Generator
# ═══════════════════════════════════════════════════════════════════════════════

async def release_notes(request: ReleaseNotesRequest) -> ReleaseNotesResponse:
    """Generate release notes from commits."""
    prompt = get_ai_prompt("release_notes_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    commits_text = "\n".join(f"- {commit}" for commit in request.commits)

    result = await chain.ainvoke({
        "version": request.version,
        "commits": commits_text,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    from datetime import date
    release_date = date.today().isoformat()

    return ReleaseNotesResponse(
        version=data.get("version", request.version),
        release_date=data.get("release_date", release_date),
        summary=data.get("summary", ""),
        features=data.get("features", []),
        bug_fixes=data.get("bug_fixes", []),
        breaking_changes=data.get("breaking_changes", []) if request.include_breaking_changes else [],
        known_issues=data.get("known_issues", []),
        upgrade_notes=data.get("upgrade_notes", "") if request.include_footer else "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 15. Smart Task Assignment
# ═══════════════════════════════════════════════════════════════════════════════

async def smart_task_assignment(request: SmartTaskAssignmentRequest) -> SmartTaskAssignmentResponse:
    """Recommend the best person to assign a task to."""
    prompt = get_ai_prompt("smart_task_assignment_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Fetch team data if project context is available
    team_data = "No specific team data available"
    if request.context.project_id:
        team_data = await _fetch_project_data(request.context)

    skills_text = ", ".join(request.required_skills) if request.required_skills else "Not specified"
    deadline_text = request.deadline or "Not specified"

    result = await chain.ainvoke({
        "task_description": request.task_description,
        "required_skills": skills_text,
        "priority": request.priority,
        "deadline": deadline_text,
        "team_data": team_data,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return SmartTaskAssignmentResponse(
        recommended_assignee=data.get("recommended_assignee", "Unassigned"),
        confidence=data.get("confidence", "medium"),
        rationale=data.get("rationale", ""),
        alternative_assignees=data.get("alternative_assignees", []),
        required_skills_match=data.get("required_skills_match", {}),
        workload_impact=data.get("workload_impact", ""),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 16. Duplicate Task Detection
# ═══════════════════════════════════════════════════════════════════════════════

async def duplicate_task_detection(request: DuplicateTaskDetectionRequest) -> DuplicateTaskResponse:
    """Detect if a new task is a duplicate of existing tasks."""
    prompt = get_ai_prompt("duplicate_task_detection_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    # Fetch existing tasks from project
    existing_tasks_text = "No existing tasks data available"
    if request.context.project_id:
        project_data = await _fetch_project_data(request.context)
        if project_data != "Project data unavailable.":
            existing_tasks_text = project_data

    result = await chain.ainvoke({
        "new_task_description": request.new_task_description,
        "existing_tasks": existing_tasks_text,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return DuplicateTaskResponse(
        is_duplicate=data.get("is_duplicate", False),
        similar_tasks=data.get("similar_tasks", []),
        similarity_scores=data.get("similarity_scores", []),
        recommendation=data.get("recommendation", "Create new task"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 17. Project Health Score
# ═══════════════════════════════════════════════════════════════════════════════

async def project_health_score(request: ProjectHealthScoreRequest) -> ProjectHealthScoreResponse:
    """Calculate a comprehensive project health score."""
    prompt = get_ai_prompt("project_health_score_v1")
    llm = get_sync_llm()
    chain = prompt | llm

    project_data = await _fetch_project_data(request.context)

    result = await chain.ainvoke({
        "project_data": project_data,
    })
    raw = result.content if hasattr(result, "content") else str(result)

    data = _parse_json_response(raw)

    return ProjectHealthScoreResponse(
        overall_score=data.get("overall_score", 50.0),
        health_status=data.get("health_status", "fair"),
        breakdown=data.get("breakdown", {}),
        recommendations=data.get("recommendations", []),
        risk_factors=data.get("risk_factors", []),
        summary=data.get("summary", ""),
    )