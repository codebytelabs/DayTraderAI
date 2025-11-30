import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { MoreVertical, TrendingUp, ExternalLink, ChevronUp, ChevronDown } from 'lucide-react';
import { PremiumCard } from '../ui/PremiumCard';
import { TrendBadge } from '../ui/StatusBadge';
import { MiniSparkline } from '../ui/TradingChart';
import { PositionsTableSkeleton } from '../ui/LoadingStates';
import type { Position } from '../../hooks/useMarketData';

interface ActivePositionsProps {
    positions: Position[];
    isLoading?: boolean;
}

type SortField = 'symbol' | 'qty' | 'avg_entry_price' | 'current_price' | 'unrealized_pl' | 'unrealized_pl_pct' | 'market_value';
type SortDirection = 'asc' | 'desc';

export function ActivePositions({ positions, isLoading }: ActivePositionsProps) {
    const [sortField, setSortField] = useState<SortField>('unrealized_pl');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

    const sortedPositions = useMemo(() => {
        return [...positions].sort((a, b) => {
            let aValue: any = a[sortField];
            let bValue: any = b[sortField];
            
            if (sortField === 'symbol') {
                aValue = aValue.toString().toLowerCase();
                bValue = bValue.toString().toLowerCase();
            }
            
            if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
            return 0;
        });
    }, [positions, sortField, sortDirection]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortField(field);
            setSortDirection('desc');
        }
    };

    const SortHeader = ({ field, children }: { field: SortField; children: React.ReactNode }) => (
        <th 
            className="cursor-pointer hover:text-white transition-colors select-none"
            onClick={() => handleSort(field)}
        >
            <div className="flex items-center gap-1">
                {children}
                <div className="flex flex-col -space-y-1">
                    <ChevronUp className={`w-3 h-3 ${sortField === field && sortDirection === 'asc' ? 'text-primary' : 'text-text-muted'}`} />
                    <ChevronDown className={`w-3 h-3 ${sortField === field && sortDirection === 'desc' ? 'text-primary' : 'text-text-muted'}`} />
                </div>
            </div>
        </th>
    );

    if (isLoading) {
        return <PositionsTableSkeleton />;
    }

    // Generate mock sparkline data for each position
    const getSparklineData = (position: Position) => {
        const basePrice = position.avg_entry_price;
        const currentPrice = position.current_price;
        const points = 20;
        const data: number[] = [];
        
        for (let i = 0; i < points; i++) {
            const progress = i / (points - 1);
            const noise = (Math.random() - 0.5) * 0.02 * basePrice;
            const value = basePrice + (currentPrice - basePrice) * progress + noise;
            data.push(value);
        }
        return data;
    };

    return (
        <PremiumCard
            title="Active Positions"
            subtitle={`${positions.length} open positions`}
            action={
                <button className="p-2 hover:bg-surface rounded-lg transition-colors text-text-secondary hover:text-white">
                    <MoreVertical className="w-5 h-5" />
                </button>
            }
        >
            <div className="overflow-x-auto -mx-6 px-6">
                <table className="premium-table">
                    <thead>
                        <tr>
                            <SortHeader field="symbol">Symbol</SortHeader>
                            <th>Side</th>
                            <SortHeader field="qty">Qty</SortHeader>
                            <SortHeader field="avg_entry_price">Entry</SortHeader>
                            <SortHeader field="current_price">Current</SortHeader>
                            <th>Trend</th>
                            <SortHeader field="unrealized_pl">P&L</SortHeader>
                            <SortHeader field="market_value">Value</SortHeader>
                            <th></th>
                        </tr>
                    </thead>
                    <tbody>
                        <AnimatePresence mode="popLayout">
                            {positions.length === 0 ? (
                                <motion.tr
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    <td colSpan={9} className="py-12 text-center">
                                        <div className="flex flex-col items-center gap-3">
                                            <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center">
                                                <TrendingUp className="w-8 h-8 text-text-muted" />
                                            </div>
                                            <p className="text-text-secondary font-medium">No active positions</p>
                                            <p className="text-text-muted text-sm">Your positions will appear here</p>
                                        </div>
                                    </td>
                                </motion.tr>
                            ) : (
                                sortedPositions.map((position, index) => {
                                    const isProfit = position.unrealized_pl >= 0;
                                    const sparklineData = getSparklineData(position);
                                    
                                    return (
                                        <motion.tr
                                            key={position.symbol}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            exit={{ opacity: 0, x: 20 }}
                                            transition={{ delay: index * 0.05 }}
                                            className="group"
                                        >
                                            <td className="py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className={`w-1 h-10 rounded-full ${position.side === 'buy' ? 'bg-success' : 'bg-danger'}`} />
                                                    <div>
                                                        <span className="font-semibold text-white">{position.symbol}</span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                <span className={`badge ${position.side === 'buy' ? 'badge-success' : 'badge-danger'}`}>
                                                    {position.side.toUpperCase()}
                                                </span>
                                            </td>
                                            <td className="text-text-primary font-medium">{position.qty}</td>
                                            <td className="text-text-secondary">${position.avg_entry_price.toFixed(2)}</td>
                                            <td className="text-text-primary font-medium">${position.current_price.toFixed(2)}</td>
                                            <td>
                                                <MiniSparkline data={sparklineData} positive={isProfit} />
                                            </td>
                                            <td className="text-right">
                                                <div className="flex flex-col items-end gap-1">
                                                    <span className={`font-semibold ${isProfit ? 'text-success' : 'text-danger'}`}>
                                                        {isProfit ? '+' : ''}{position.unrealized_pl.toFixed(2)}
                                                    </span>
                                                    <TrendBadge value={position.unrealized_pl_pct} />
                                                </div>
                                            </td>
                                            <td className="text-right">
                                                <span className="font-semibold text-white">
                                                    ${position.market_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                                </span>
                                            </td>
                                            <td className="text-right">
                                                <button className="p-2 opacity-0 group-hover:opacity-100 hover:bg-surface rounded-lg transition-all text-text-secondary hover:text-white">
                                                    <ExternalLink className="w-4 h-4" />
                                                </button>
                                            </td>
                                        </motion.tr>
                                    );
                                })
                            )}
                        </AnimatePresence>
                    </tbody>
                </table>
            </div>
            
            {positions.length > 0 && (
                <motion.div
                    className="mt-6 pt-4 border-t border-glass-border flex items-center justify-between"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                >
                    <div className="flex items-center gap-6">
                        <div>
                            <p className="text-xs text-text-muted mb-1">Total Value</p>
                            <p className="text-lg font-bold text-white">
                                ${positions.reduce((sum, p) => sum + p.market_value, 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </p>
                        </div>
                        <div>
                            <p className="text-xs text-text-muted mb-1">Total P&L</p>
                            <p className={`text-lg font-bold ${positions.reduce((sum, p) => sum + p.unrealized_pl, 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                                {positions.reduce((sum, p) => sum + p.unrealized_pl, 0) >= 0 ? '+' : ''}
                                ${positions.reduce((sum, p) => sum + p.unrealized_pl, 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                            </p>
                        </div>
                    </div>
                    <button className="btn-secondary text-sm">
                        View All Positions
                    </button>
                </motion.div>
            )}
        </PremiumCard>
    );
}
