import React from 'react';
import { MoreVertical, TrendingUp, TrendingDown } from 'lucide-react';
import { GlassCard } from '../layout/GlassCard';
import type { Position } from '../../hooks/useMarketData';

interface ActivePositionsProps {
    positions: Position[];
}

export function ActivePositions({ positions }: ActivePositionsProps) {
    return (
        <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-glass-text-primary">Active Positions</h2>
                <button className="p-2 hover:bg-glass-surface rounded-lg transition-colors text-glass-text-secondary">
                    <MoreVertical className="w-5 h-5" />
                </button>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full">
                    <thead>
                        <tr className="text-left text-sm text-glass-text-secondary border-b border-glass-border">
                            <th className="pb-4 font-medium">Symbol</th>
                            <th className="pb-4 font-medium">Side</th>
                            <th className="pb-4 font-medium">Entry</th>
                            <th className="pb-4 font-medium">Current</th>
                            <th className="pb-4 font-medium">P&L</th>
                            <th className="pb-4 font-medium text-right">Value</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {positions.length === 0 ? (
                            <tr>
                                <td colSpan={6} className="py-8 text-center text-glass-text-secondary">
                                    No active positions
                                </td>
                            </tr>
                        ) : (
                            positions.map((position) => (
                                <tr key={position.symbol} className="group border-b border-glass-border/50 last:border-0 hover:bg-glass-surface/30 transition-colors">
                                    <td className="py-4 font-medium text-glass-text-primary">
                                        {position.symbol}
                                    </td>
                                    <td className="py-4">
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${position.side === 'buy'
                                            ? 'bg-success/10 text-success'
                                            : 'bg-danger/10 text-danger'
                                            }`}>
                                            {position.side.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="py-4 text-glass-text-secondary">
                                        ${position.avg_entry_price.toFixed(2)}
                                    </td>
                                    <td className="py-4 text-glass-text-primary">
                                        ${position.current_price.toFixed(2)}
                                    </td>
                                    <td className="py-4">
                                        <div className={`flex items-center ${position.unrealized_pl >= 0 ? 'text-success' : 'text-danger'
                                            }`}>
                                            {position.unrealized_pl >= 0 ? (
                                                <TrendingUp className="w-3 h-3 mr-1" />
                                            ) : (
                                                <TrendingDown className="w-3 h-3 mr-1" />
                                            )}
                                            <span className="font-medium">
                                                {position.unrealized_pl >= 0 ? '+' : ''}{position.unrealized_pl.toFixed(2)} ({position.unrealized_pl_pct.toFixed(2)}%)
                                            </span>
                                        </div>
                                    </td>
                                    <td className="py-4 text-right text-glass-text-primary font-medium">
                                        ${position.market_value.toFixed(2)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </GlassCard>
    );
}
;
