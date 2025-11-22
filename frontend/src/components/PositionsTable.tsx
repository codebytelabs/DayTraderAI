import React from 'react';
import { ArrowUpRight, ArrowDownRight, MoreHorizontal } from 'lucide-react';

interface Position {
    symbol: string;
    qty: number;
    side: string;
    avg_entry_price: number;
    current_price: number;
    unrealized_pl: number;
    unrealized_pl_pct: number;
    market_value: number;
}

interface PositionsTableProps {
    positions: Position[];
}

export const PositionsTable: React.FC<PositionsTableProps> = ({ positions }) => {
    if (positions.length === 0) {
        return (
            <div className="text-center py-12 text-slate-500">
                No open positions
            </div>
        );
    }

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
                <thead className="text-slate-400 border-b border-slate-800">
                    <tr>
                        <th className="pb-3 font-medium">Symbol</th>
                        <th className="pb-3 font-medium text-right">Qty</th>
                        <th className="pb-3 font-medium text-right">Entry</th>
                        <th className="pb-3 font-medium text-right">Price</th>
                        <th className="pb-3 font-medium text-right">Value</th>
                        <th className="pb-3 font-medium text-right">P/L ($)</th>
                        <th className="pb-3 font-medium text-right">P/L (%)</th>
                        <th className="pb-3 font-medium"></th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                    {positions.map((pos) => {
                        const isProfit = pos.unrealized_pl >= 0;
                        return (
                            <tr key={pos.symbol} className="group hover:bg-slate-800/50 transition-colors">
                                <td className="py-4 font-medium text-white">
                                    <div className="flex items-center">
                                        <span className={`w-1 h-8 rounded-full mr-3 ${pos.side === 'buy' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                                        <div>
                                            <div>{pos.symbol}</div>
                                            <div className="text-xs text-slate-500 uppercase">{pos.side}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="py-4 text-right text-slate-300">{pos.qty}</td>
                                <td className="py-4 text-right text-slate-300">${pos.avg_entry_price.toFixed(2)}</td>
                                <td className="py-4 text-right text-slate-300">${pos.current_price.toFixed(2)}</td>
                                <td className="py-4 text-right text-slate-300">${pos.market_value.toFixed(2)}</td>
                                <td className={`py-4 text-right font-medium ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                                    {pos.unrealized_pl > 0 ? '+' : ''}{pos.unrealized_pl.toFixed(2)}
                                </td>
                                <td className={`py-4 text-right font-medium ${isProfit ? 'text-emerald-500' : 'text-rose-500'}`}>
                                    <div className="flex items-center justify-end">
                                        {isProfit ? <ArrowUpRight className="w-4 h-4 mr-1" /> : <ArrowDownRight className="w-4 h-4 mr-1" />}
                                        {pos.unrealized_pl_pct.toFixed(2)}%
                                    </div>
                                </td>
                                <td className="py-4 text-right">
                                    <button className="p-1 text-slate-500 hover:text-white rounded hover:bg-slate-700">
                                        <MoreHorizontal className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
    );
};
