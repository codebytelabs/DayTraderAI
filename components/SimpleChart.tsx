import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { PerformanceDataPoint } from "../types";

interface SimpleChartProps {
  data: PerformanceDataPoint[];
}

export const SimpleChart: React.FC<SimpleChartProps> = ({ data }) => {
  console.log("[SimpleChart] Data received:", data);

  if (data.length === 0) {
    return (
      <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50 h-80 flex items-center justify-center">
        <div className="text-center text-slate-500">
          <div className="flex flex-col items-center gap-3">
            <span className="text-4xl">📈</span>
            <span>No performance data available</span>
          </div>
        </div>
      </div>
    );
  }

  const minValue = Math.min(...data.map(d => d.close));
  const maxValue = Math.max(...data.map(d => d.close));
  const startValue = data[0].close;
  const endValue = data[data.length - 1].close;
  const change = endValue - startValue;
  const changePercent = ((change / startValue) * 100).toFixed(2);
  const isPositive = change >= 0;

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xl">📊</span>
            <h3 className="text-xl font-bold text-white">Portfolio Equity</h3>
          </div>
          <p className="text-xs text-slate-400">
            {data.length} data points from last trading day
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-white mb-1">
            ${endValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-bold ${
            isPositive 
              ? 'bg-emerald-500/20 text-emerald-400' 
              : 'bg-rose-500/20 text-rose-400'
          }`}>
            <span>{isPositive ? '↑' : '↓'}</span>
            <span>{change.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}</span>
            <span>({changePercent}%)</span>
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <defs>
            <linearGradient id="lineGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity={0.8}/>
              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0.8}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
          <XAxis
            dataKey="timestamp"
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#94a3b8' }}
            tickFormatter={(ts: number) => {
              const date = new Date(ts * 1000);
              const firstDate = new Date(data[0].timestamp * 1000);
              const lastDate = new Date(data[data.length - 1].timestamp * 1000);
              const daysDiff = (lastDate.getTime() - firstDate.getTime()) / (1000 * 60 * 60 * 24);
              
              if (daysDiff > 1) {
                return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
              } else {
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
              }
            }}
          />
          <YAxis
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#94a3b8' }}
            domain={[minValue * 0.9995, maxValue * 1.0005]}
            tickFormatter={(value: number) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{ 
              backgroundColor: '#1e293b', 
              border: '1px solid #475569',
              borderRadius: '8px',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.3)'
            }}
            labelStyle={{ color: '#94a3b8', fontSize: '12px' }}
            itemStyle={{ color: '#10b981', fontSize: '13px', fontWeight: 'bold' }}
            labelFormatter={(ts: number) => new Date(ts * 1000).toLocaleString()}
            formatter={(value: number) => [`$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Equity']}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="url(#lineGradient)"
            strokeWidth={3}
            dot={false}
            animationDuration={500}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
