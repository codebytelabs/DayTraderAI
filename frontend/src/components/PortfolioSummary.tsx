import React, { useState } from 'react';
import { TrendingUp, TrendingDown, DollarSign, Wallet, Activity } from 'lucide-react';
import { PortfolioChart } from './PortfolioChart';
import { PositionsTable } from './PositionsTable';
import { useWebSocket } from '../hooks/useWebSocket';

interface Metrics {
    equity: number;
    cash: number;
    buying_power: number;
    daily_pl: number;
    daily_pl_pct: number;
    win_rate: number;
    profit_factor: number;
}

export const PortfolioSummary: React.FC = () => {
    const [metrics, setMetrics] = useState<Metrics | null>(null);
    const [positions, setPositions] = useState<any[]>([]);
    const [chartData] = useState<any[]>([]);

    useWebSocket({
        url: 'ws://localhost:8006/ws/stream',
        onMessage: (data) => {
            if (data.type === 'snapshot') {
                if (data.payload.metrics) {
                    setMetrics(data.payload.metrics);
                }
                if (data.payload.positions) {
                    setPositions(data.payload.positions);
                }
                // In a real app, we'd append to chart history here
                // For now, we'll just update the current point if we had history
            }
        },
    });

    if (!metrics) {
        return (
            <div className="p-6 bg-slate-900 rounded-xl border border-slate-800 animate-pulse">
                <div className="h-8 bg-slate-800 rounded w-1/3 mb-4"></div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className="h-24 bg-slate-800 rounded"></div>
                    <div className="h-24 bg-slate-800 rounded"></div>
                    <div className="h-24 bg-slate-800 rounded"></div>
                </div>
            </div>
        );
    }

    const isProfit = metrics.daily_pl >= 0;

    return (
        <div className="space-y-6">
            {/* Top Metrics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-900 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 text-sm">Total Equity</span>
                        <DollarSign className="w-4 h-4 text-emerald-500" />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        ${metrics.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        Cash: ${metrics.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                </div>

                <div className="p-4 bg-slate-900 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 text-sm">Daily P/L</span>
                        {isProfit ? <TrendingUp className="w-4 h-4 text-emerald-500" /> : <TrendingDown className="w-4 h-4 text-rose-500" />}
                    </div>
                    <div className={`text-2xl font-bold ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {isProfit ? '+' : ''}{metrics.daily_pl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className={`text-xs font-medium mt-1 ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                        {isProfit ? '+' : ''}{metrics.daily_pl_pct.toFixed(2)}%
                    </div>
                </div>

                <div className="p-4 bg-slate-900 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 text-sm">Buying Power</span>
                        <Wallet className="w-4 h-4 text-blue-500" />
                    </div>
                    <div className="text-2xl font-bold text-white">
                        ${metrics.buying_power.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        Available for trading
                    </div>
                </div>

                <div className="p-4 bg-slate-900 rounded-xl border border-slate-800">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-slate-400 text-sm">Performance</span>
                        <Activity className="w-4 h-4 text-purple-500" />
                    </div>
                    <div className="flex items-end space-x-2">
                        <div className="text-2xl font-bold text-white">
                            {(metrics.win_rate * 100).toFixed(1)}%
                        </div>
                        <div className="text-sm text-slate-500 mb-1">Win Rate</div>
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                        Profit Factor: {metrics.profit_factor.toFixed(2)}
                    </div>
                </div>
            </div>

            {/* Chart Section */}
            <div className="p-6 bg-slate-900 rounded-xl border border-slate-800">
                <h3 className="text-lg font-semibold text-white mb-4">Equity Curve</h3>
                <PortfolioChart data={chartData} />
            </div>

            {/* Positions Section */}
            <div className="p-6 bg-slate-900 rounded-xl border border-slate-800">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-white">Open Positions</h3>
                    <span className="px-2 py-1 bg-slate-800 rounded text-xs text-slate-400">
                        {positions.length} Active
                    </span>
                </div>
                <PositionsTable positions={positions} />
            </div>
        </div>
    );
};
