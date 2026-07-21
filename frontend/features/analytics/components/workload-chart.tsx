'use client';

import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts';

const DATA = [
  { member: 'Alex', tasks: 8 },
  { member: 'Priya', tasks: 14 },
  { member: 'Jordan', tasks: 6 },
  { member: 'Sam', tasks: 11 },
  { member: 'Morgan', tasks: 9 },
  { member: 'Casey', tasks: 16 },
];

interface WorkloadChartProps {
  data?: Array<{ member: string; tasks: number }>;
}

const OVERLOAD_THRESHOLD = 12;

export function WorkloadChart({ data }: WorkloadChartProps) {
  const chartData = data && data.length > 0 ? data : [];

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-60 text-sm text-slate-500">
        No team workload data available yet
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
        <XAxis dataKey="member" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#94a3b8' }}
        />
        <Bar dataKey="tasks" radius={[4, 4, 0, 0]}>
          {chartData.map((entry) => (
            <Cell
              key={entry.member}
              fill={entry.tasks >= OVERLOAD_THRESHOLD ? '#f59e0b' : '#6366f1'}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
