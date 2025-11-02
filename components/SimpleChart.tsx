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
      <div className="bg-brand-surface p-4 rounded-lg h-72 flex items-center justify-center">
        <p className="text-brand-text-secondary">No data available</p>
      </div>
    );
  }

  // Calculate stats
  const minValue = Math.min(...data.map(d => d.close));
  const maxValue = Math.max(...data.map(d => d.close));
  const startValue = data[0].close;
  const endValue = data[data.length - 1].close;
  const change = endValue - startValue;
  const changePercent = ((change / startValue) * 100).toFixed(2);

  return (
    <div className="bg-brand-surface p-4 rounded-lg h-72">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold text-brand-text">
            Portfolio Equity
          </h3>
          <p className="text-sm text-brand-text-secondary">
            {data.length} data points from last trading day
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-brand-text">
            ${endValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
          <div className={`text-sm font-semibold ${change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
            {change >= 0 ? '+' : ''}{change.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} ({changePercent}%)
          </div>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="80%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2A2C3F" />
          <XAxis
            dataKey="timestamp"
            stroke="#A3A3C2"
            tick={{ fontSize: 11 }}
            tickFormatter={(ts: number) => {
              const date = new Date(ts * 1000);
              // If data spans more than 1 day, show date. Otherwise show time.
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
            stroke="#A3A3C2"
            tick={{ fontSize: 11 }}
            domain={[minValue * 0.9995, maxValue * 1.0005]}
            tickFormatter={(value: number) => `$${(value / 1000).toFixed(0)}k`}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #059669' }}
            labelFormatter={(ts: number) => new Date(ts * 1000).toLocaleString()}
            formatter={(value: number) => [`$${value.toLocaleString('en-US', { minimumFractionDigits: 2 })}`, 'Equity']}
          />
          <Line
            type="monotone"
            dataKey="close"
            stroke="#059669"
            strokeWidth={2}
            dot={false}
            animationDuration={300}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
