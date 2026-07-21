'use client';

import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const DATA = [
  { name: 'Active', value: 12, color: '#6366f1' },
  { name: 'On Hold', value: 4, color: '#f59e0b' },
  { name: 'Completed', value: 8, color: '#10b981' },
  { name: 'Archived', value: 3, color: '#475569' },
];

interface ProjectStatusChartProps {
  data?: Array<{ name: string; value: number; color: string }>;
}

export function ProjectStatusChart({ data }: ProjectStatusChartProps) {
  const chartData = data && data.length > 0 ? data : [
    { name: 'Active', value: 0, color: '#6366f1' },
    { name: 'On Hold', value: 0, color: '#f59e0b' },
    { name: 'Completed', value: 0, color: '#10b981' },
    { name: 'Archived', value: 0, color: '#475569' },
  ];

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={90}
          paddingAngle={3}
          dataKey="value"
        >
          {chartData.map((entry) => (
            <Cell key={entry.name} fill={entry.color} stroke="transparent" />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#94a3b8' }}
        />
        <Legend
          iconType="circle"
          iconSize={8}
          formatter={(value) => <span style={{ color: '#94a3b8', fontSize: 12 }}>{value}</span>}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
