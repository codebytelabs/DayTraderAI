import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { GlassCard } from './layout/GlassCard';
import type { PortfolioHistoryPoint } from '../hooks/useMarketData';

interface PortfolioChartProps {
    data: PortfolioHistoryPoint[];
}

export function PortfolioChart({ data }: PortfolioChartProps) {
    return (
        <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-lg font-semibold text-glass-text-primary">Portfolio Performance</h2>
                    <p className="text-sm text-glass-text-secondary">Net Liquidation Value</p>
                </div>
                <div className="flex space-x-2">
                    {['1D', '1W', '1M', '3M', '1Y', 'ALL'].map((period) => (
                        <button
                            key={period}
                            className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${period === '1D'
                                ? 'bg-primary text-white'
                                : 'text-glass-text-secondary hover:bg-glass-surface hover:text-glass-text-primary'
                                }`}
                        >
                            {period}
                        </button>
                    ))}
                </div>
            </div>

            <div className="h-[300px] w-full">
                <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3} />
                                <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-glass-border)" vertical={false} />
                        <XAxis
                            dataKey="timestamp"
                            stroke="var(--color-glass-text-secondary)"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(ts) => new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        />
                        <YAxis
                            stroke="var(--color-glass-text-secondary)"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={(value) => `$${value.toLocaleString()}`}
                            domain={['auto', 'auto']}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: 'rgba(17, 25, 40, 0.9)',
                                backdropFilter: 'blur(12px)',
                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                borderRadius: '0.75rem',
                                color: '#fff',
                            }}
                            itemStyle={{ color: '#fff' }}
                            labelStyle={{ color: 'rgba(255, 255, 255, 0.7)' }}
                            formatter={(value: number) => [`$${value.toLocaleString()}`, 'Value']}
                            labelFormatter={(label) => new Date(label * 1000).toLocaleString()}
                        />
                        <Area
                            type="monotone"
                            dataKey="equity"
                            stroke="var(--color-primary)"
                            strokeWidth={2}
                            fillOpacity={1}
                            fill="url(#colorValue)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </GlassCard>
    );
}
;
