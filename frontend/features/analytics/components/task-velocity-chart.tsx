'use client';

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';

const DATA = [
  { week: 'W1', completed: 14 },
  { week: 'W2', completed: 22 },
  { week: 'W3', completed: 18 },
  { week: 'W4', completed: 31 },
  { week: 'W5', completed: 27 },
  { week: 'W6', completed: 35 },
  { week: 'W7', completed: 29 },
  { week: 'W8', completed: 41 },
];

interface TaskVelocityChartProps {
  data?: Array<{ week: string; completed: number }>;
}

export function TaskVelocityChart({ data }: TaskVelocityChartProps) {
  const chartData = data && data.length > 0 ? data : [
    { week: 'W1', completed: 0 },
    { week: 'W2', completed: 0 },
    { week: 'W3', completed: 0 },
    { week: 'W4', completed: 0 },
    { week: 'W5', completed: 0 },
    { week: 'W6', completed: 0 },
    { week: 'W7', completed: 0 },
    { week: 'W8', completed: 0 },
  ];

  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="week" tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#94a3b8' }}
        />
        <Line
          type="monotone"
          dataKey="completed"
          stroke="#6366f1"
          strokeWidth={2}
          dot={{ fill: '#6366f1', r: 3 }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
