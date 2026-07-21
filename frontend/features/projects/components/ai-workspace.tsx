'use client';

import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { aiApi } from '@/services/ai-api';
import { useSelector } from 'react-redux';
import { RootState } from '@/store';
import { Loader2, Sparkles, Brain, GitBranch, FileText, MessageSquare, Calendar, AlertTriangle, Users, Target } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

interface AIWorkspaceProps {
  projectId: string;
}

type AITool = 'chat' | 'task-breakdown' | 'sprint-planning' | 'project-summary' | 'doc-qa' | 'meeting-summary' | 'deadline-prediction' | 'risk-analysis' | 'workload-suggestion';

const TOOLS: { key: AITool; label: string; icon: React.ReactNode; color: string }[] = [
  { key: 'chat', label: 'AI Chat', icon: <MessageSquare className="h-4 w-4" />, color: 'text-indigo-400' },
  { key: 'task-breakdown', label: 'Task Breakdown', icon: <Brain className="h-4 w-4" />, color: 'text-emerald-400' },
  { key: 'sprint-planning', label: 'Sprint Planner', icon: <GitBranch className="h-4 w-4" />, color: 'text-amber-400' },
  { key: 'project-summary', label: 'Project Summary', icon: <FileText className="h-4 w-4" />, color: 'text-violet-400' },
  { key: 'doc-qa', label: 'Doc Q&A (RAG)', icon: <Sparkles className="h-4 w-4" />, color: 'text-pink-400' },
  { key: 'meeting-summary', label: 'Meeting Summary', icon: <Users className="h-4 w-4" />, color: 'text-cyan-400' },
  { key: 'deadline-prediction', label: 'Deadline Predict', icon: <Calendar className="h-4 w-4" />, color: 'text-red-400' },
  { key: 'risk-analysis', label: 'Risk Analysis', icon: <AlertTriangle className="h-4 w-4" />, color: 'text-orange-400' },
  { key: 'workload-suggestion', label: 'Workload Suggest', icon: <Target className="h-4 w-4" />, color: 'text-teal-400' },
];

export function AIWorkspace({ projectId }: AIWorkspaceProps) {
  const { activeOrgId } = useSelector((s: RootState) => s.org);
  const [activeTool, setActiveTool] = useState<AITool>('chat');
  const [input, setInput] = useState('');
  const [result, setResult] = useState<any>(null);

  const context = { project_id: projectId, org_id: activeOrgId || undefined };

  const mutation = useMutation({
    mutationFn: async () => {
      setResult(null);
      switch (activeTool) {
        case 'chat':
          return aiApi.chat({ message: input, context });
        case 'task-breakdown':
          return aiApi.taskBreakdown({ task_description: input, context });
        case 'sprint-planning':
          return aiApi.sprintPlanning({ backlog_items: input.split('\n').filter(Boolean), context });
        case 'project-summary':
          return aiApi.projectSummary({ context });
        case 'doc-qa':
          return aiApi.docQA({ question: input, context });
        case 'meeting-summary':
          return aiApi.meetingSummary({ meeting_notes: input, context });
        case 'deadline-prediction':
          return aiApi.deadlinePrediction({ include_all_pending: true, context });
        case 'risk-analysis':
          return aiApi.riskAnalysis({ context });
        case 'workload-suggestion':
          return aiApi.workloadSuggestion({ upcoming_tasks: input.split('\n').filter(Boolean), context });
        default:
          throw new Error('Unknown tool');
      }
    },
    onSuccess: (data) => setResult(data),
    onError: (err: any) => toast.error(err.message || 'AI request failed'),
  });

  const getPlaceholder = () => {
    switch (activeTool) {
      case 'chat': return 'Ask anything about your project...';
      case 'task-breakdown': return 'Describe the complex task to break down...';
      case 'sprint-planning': return 'Enter backlog items (one per line)...';
      case 'project-summary': return 'Click generate for an AI project summary';
      case 'doc-qa': return 'Ask a question about your project documents...';
      case 'meeting-summary': return 'Paste meeting notes or transcript...';
      case 'deadline-prediction': return 'Click predict to analyze deadlines';
      case 'risk-analysis': return 'Click analyze to identify project risks';
      case 'workload-suggestion': return 'Enter upcoming tasks (one per line)...';
    }
  };

  const needsInput = !['project-summary', 'deadline-prediction', 'risk-analysis'].includes(activeTool);

  return (
    <div className="flex flex-col gap-6">
      <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-indigo-400" /> AI Workspace
      </h3>

      {/* Tool Selector */}
      <div className="flex flex-wrap gap-2">
        {TOOLS.map(tool => (
          <button
            key={tool.key}
            onClick={() => { setActiveTool(tool.key); setResult(null); setInput(''); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              activeTool === tool.key
                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                : 'bg-slate-900/30 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
            }`}
          >
            <span className={tool.color}>{tool.icon}</span>
            {tool.label}
          </button>
        ))}
      </div>

      {/* Input Area */}
      {needsInput && (
        <div className="flex flex-col gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={getPlaceholder()}
            rows={4}
            className="bg-slate-900 border border-slate-800 text-slate-100 rounded-xl p-4 text-sm outline-none focus:border-indigo-500/50 resize-none"
          />
          <Button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !input.trim()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white self-start"
          >
            {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
            {mutation.isPending ? 'Processing...' : `Generate ${TOOLS.find(t => t.key === activeTool)?.label || 'Result'}`}
          </Button>
        </div>
      )}

      {/* Auto-generate buttons for tools without input */}
      {!needsInput && (
        <Button
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          className="bg-indigo-600 hover:bg-indigo-700 text-white self-start"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
          {mutation.isPending ? 'Processing...' : `Generate ${TOOLS.find(t => t.key === activeTool)?.label || 'Result'}`}
        </Button>
      )}

      {/* Result */}
      {mutation.isPending && (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin text-indigo-400" />
        </div>
      )}

      {result && (
        <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 overflow-auto max-h-[600px] shadow-lg">
          <pre className="text-sm text-slate-200 whitespace-pre-wrap font-sans leading-relaxed">
            {typeof result === 'string'
              ? result
              : result?.content
              ? result.content
              : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}