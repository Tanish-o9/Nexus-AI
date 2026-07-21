'use client';

import {
  Briefcase, Layers, TrendingUp, Sparkles, GitPullRequest, Bot, ShieldCheck,
  CheckCircle2, ArrowRight, Activity, Users, FileText, Compass, Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { useProjects } from '@/features/projects/hooks/use-projects';
import Link from 'next/link';

export default function DashboardPage() {
  const { activeOrgId } = useSelector((s: RootState) => s.org);
  const { data: projectsData, isLoading } = useProjects({ organizationId: activeOrgId || undefined });

  const projects = projectsData?.results || [];
  const activeCount = projects.filter(p => p.status === 'active').length;
  const completedCount = projects.filter(p => p.status === 'completed').length;
  
  // Calculate average progress
  const avgProgress = projects.length > 0
    ? Math.round(projects.reduce((acc, p) => acc + (p.progress || 0), 0) / projects.length)
    : 0;

  // Calculate health breakdown
  const onTrackCount = projects.filter(p => p.health === 'on_track').length;
  const criticalCount = projects.filter(p => p.health === 'critical').length;

  return (
    <div className="flex flex-col gap-8 p-8 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 glass-card-3d rounded-2xl p-6 shadow-[0_20px_50px_rgba(0,0,0,0.5)]">
        <div>
          <div className="flex items-center gap-2.5 mb-1">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse shadow shadow-emerald-400/50" />
            <span className="text-xs font-semibold text-emerald-400 tracking-wider uppercase">Enterprise PM Suite</span>
          </div>
          <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight">Executive Dashboard</h1>
          <p className="text-sm text-slate-400 mt-1">
            Welcome back! Monitor project health, team velocity, and AI-driven sprint management.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/projects/">
            <Button className="glow-button-3d bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm px-5 py-2.5 rounded-xl border border-indigo-400/30">
              <Briefcase className="h-4 w-4 mr-2" />
              View Projects Hub
            </Button>
          </Link>
          <Link href="/ai-chat/">
            <Button className="glass-card-3d bg-slate-900/80 hover:bg-slate-800 text-slate-200 font-semibold text-sm px-4 py-2.5 rounded-xl border border-slate-700">
              <Bot className="h-4 w-4 mr-2 text-indigo-400" />
              Launch AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Stat Metric Cards */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard
          icon={<Briefcase className="h-5 w-5" />}
          color="indigo"
          label="Active Projects"
          value={isLoading ? '...' : String(activeCount)}
          sub={`${completedCount} completed projects in workspace`}
        />
        <StatCard
          icon={<Layers className="h-5 w-5" />}
          color="violet"
          label="Average Progress"
          value={isLoading ? '...' : `${avgProgress}%`}
          sub="Overall completion rate across tracked tasks"
        />
        <StatCard
          icon={<TrendingUp className="h-5 w-5" />}
          color="emerald"
          label="Project Health"
          value={isLoading ? '...' : `${onTrackCount} / ${projects.length || 1}`}
          sub={`${criticalCount} critical projects needing attention`}
        />
      </section>

      {/* About The Platform Section */}
      <section className="glass-card-3d rounded-2xl p-7 flex flex-col gap-5 border border-indigo-500/20 shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-500 to-violet-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">About Nexus PM Platform</h2>
            <p className="text-xs text-slate-400">Next-Generation AI-Driven Project & Product Management Engine</p>
          </div>
        </div>

        <p className="text-slate-300 text-sm leading-relaxed">
          <strong className="text-indigo-300 font-semibold">Nexus PM</strong> is an all-in-one enterprise project management web application built for modern software teams, engineering leads, and product owners. It unifies high-cohesion feature architecture with real-time Kanban boards, code-to-task GitHub commit tracking, live team workload analytics, auto-provisioned sprint reports, and a suite of 9 specialized AI assistant tools.
        </p>
      </section>

      {/* Primary Uses & Key Capabilities Section */}
      <section className="flex flex-col gap-5">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Compass className="h-5 w-5 text-indigo-400" />
            How To Use This Web Application
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">Explore key features and step-by-step workflow capabilities</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <UseCaseCard
            icon={<CheckCircle2 className="h-5 w-5 text-indigo-400" />}
            title="1. 4-Stage Task Pipeline & Owner Review"
            description="Create tasks with mandatory title, description, assignee, priority, and due date. Move tasks from To Do ➔ 'Chalo Start Karte Hain' (In Progress) ➔ Push Code via GitHub (In Review) ➔ Owner Rating & Approval (Done)."
            badge="Core Workflow"
            badgeColor="bg-indigo-500/10 text-indigo-300 border-indigo-500/20"
          />

          <UseCaseCard
            icon={<Bot className="h-5 w-5 text-violet-400" />}
            title="2. Nexus AI Workspace & Assistant"
            description="Leverage 9 AI engineering tools: Task Breakdown, Sprint Planning, Project Health Summary, Doc Q&A (RAG), Meeting Notes, Deadline Predictor, Risk Analysis, and Workload Suggestion with smart database context."
            badge="AI Copilot"
            badgeColor="bg-violet-500/10 text-violet-300 border-violet-500/20"
          />

          <UseCaseCard
            icon={<GitPullRequest className="h-5 w-5 text-emerald-400" />}
            title="3. GitHub Integration & Commit Sync"
            description="Connect repositories directly to your projects. Simulate or record actual code commits to record author details, commit hashes, modified files, and automatically transition tasks into Review status."
            badge="Code Automation"
            badgeColor="bg-emerald-500/10 text-emerald-300 border-emerald-500/20"
          />

          <UseCaseCard
            icon={<Activity className="h-5 w-5 text-amber-400" />}
            title="4. Live Analytics & Sprint Performance Reports"
            description="Track real team workload per member, inspect 8-week task velocity, monitor project status distributions, and generate automated weekly/monthly executive sprint performance reports."
            badge="Realtime Insights"
            badgeColor="bg-amber-500/10 text-amber-300 border-amber-500/20"
          />
        </div>
      </section>

      {/* Quick Action Navigation Grid */}
      <section className="glass-card-3d rounded-2xl p-7 flex flex-col gap-4">
        <div className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-amber-400" />
          <h2 className="text-base font-bold text-slate-100">Quick Navigation Shortcuts</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <QuickShortcutLink
            href="/projects"
            icon={<Briefcase className="h-4 w-4 text-indigo-400" />}
            title="Projects Hub"
            subtitle="Kanban, Milestones, Sprints & Repos"
          />
          <QuickShortcutLink
            href="/ai-chat"
            icon={<Bot className="h-4 w-4 text-violet-400" />}
            title="AI Chat Assistant"
            subtitle="Ask questions & run AI tools"
          />
          <QuickShortcutLink
            href="/analytics"
            icon={<Activity className="h-4 w-4 text-emerald-400" />}
            title="Global Analytics"
            subtitle="Live velocity & team workloads"
          />
          <QuickShortcutLink
            href="/settings"
            icon={<ShieldCheck className="h-4 w-4 text-amber-400" />}
            title="Account Settings"
            subtitle="Profile, security & preferences"
          />
        </div>
      </section>
    </div>
  );
}

const COLOR = {
  indigo: { ring: 'text-indigo-400', glow: 'bg-indigo-500/10', sub: 'text-indigo-300' },
  violet: { ring: 'text-violet-400', glow: 'bg-violet-500/10', sub: 'text-violet-300' },
  emerald: { ring: 'text-emerald-400', glow: 'bg-emerald-500/10', sub: 'text-emerald-300' },
} as const;

function StatCard({
  icon, color, label, value, sub,
}: {
  icon: React.ReactNode;
  color: keyof typeof COLOR;
  label: string;
  value: string;
  sub: string;
}) {
  const c = COLOR[color];
  return (
    <div className="glass-card-3d card-3d-tilt relative overflow-hidden rounded-2xl p-6 shadow-2xl">
      <div className={`absolute -top-6 -right-6 h-36 w-36 ${c.glow} rounded-full blur-3xl animate-pulse-glow`} />
      <div className={`flex items-center gap-3 ${c.ring}`}>
        <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 shadow-md">
          {icon}
        </div>
        <h3 className="font-semibold text-xs tracking-wider uppercase">{label}</h3>
      </div>
      <p className="text-4xl font-black mt-4 tracking-tight text-slate-100">{value}</p>
      <span className={`text-xs mt-2 block font-medium ${c.sub}`}>{sub}</span>
    </div>
  );
}

function UseCaseCard({
  icon, title, description, badge, badgeColor
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  badge: string;
  badgeColor: string;
}) {
  return (
    <div className="glass-card-3d card-3d-tilt rounded-2xl p-6 flex flex-col justify-between gap-4">
      <div className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 shadow-md">
              {icon}
            </div>
            <h3 className="text-sm font-bold text-slate-100">{title}</h3>
          </div>
          <span className={`text-[10px] font-semibold px-2.5 py-0.5 rounded-full border ${badgeColor}`}>
            {badge}
          </span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed mt-1">{description}</p>
      </div>
    </div>
  );
}

function QuickShortcutLink({
  href, icon, title, subtitle
}: {
  href: string;
  icon: React.ReactNode;
  title: string;
  subtitle: string;
}) {
  return (
    <Link href={href} className="group">
      <div className="glass-card-3d card-3d-tilt rounded-xl p-4 flex flex-col gap-1.5 transition-all">
        <div className="flex items-center justify-between">
          <div className="p-2 rounded-lg bg-slate-950/80 border border-slate-800">
            {icon}
          </div>
          <ArrowRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
        </div>
        <h4 className="text-xs font-bold text-slate-200 group-hover:text-indigo-300 transition-colors mt-1">{title}</h4>
        <p className="text-[11px] text-slate-500 line-clamp-1">{subtitle}</p>
      </div>
    </Link>
  );
}
