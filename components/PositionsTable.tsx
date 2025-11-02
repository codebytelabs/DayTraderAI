
import React from 'react';
import { Position, OrderSide } from '../types';
import { MinusCircleIcon } from './icons/MinusCircleIcon';

interface PositionsTableProps {
  positions: Position[];
  closePosition: (positionId: string) => void;
}

export const PositionsTable: React.FC<PositionsTableProps> = ({ positions, closePosition }) => {
  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50 overflow-hidden">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-xl font-bold text-white">Open Positions</h3>
        <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-sm font-semibold">
          {positions.length}
        </span>
      </div>
      <div className="overflow-x-auto">
        <div className="max-h-[400px] overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700/50 sticky top-0 bg-slate-900/90 backdrop-blur-sm">
              <tr>
                <th scope="col" className="px-4 py-4 text-left font-semibold">Symbol</th>
                <th scope="col" className="px-4 py-4 text-left font-semibold">Side</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Qty</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">P/L ($)</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">P/L (%)</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Market Value</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Take Profit</th>
                <th scope="col" className="px-4 py-4 text-right font-semibold">Stop Loss</th>
                <th scope="col" className="px-4 py-4 text-center font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {positions.length > 0 ? positions.map((pos) => (
                <tr key={pos.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-4 font-bold text-white">{pos.symbol}</td>
                  <td className="px-4 py-4">
                    <span className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                      pos.side === OrderSide.BUY 
                        ? 'bg-emerald-500/20 text-emerald-400' 
                        : 'bg-rose-500/20 text-rose-400'
                    }`}>
                      {pos.side === OrderSide.BUY ? 'LONG' : 'SHORT'}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-right text-slate-300">{pos.qty}</td>
                  <td className={`px-4 py-4 text-right font-bold ${
                    pos.unrealizedPl >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    ${pos.unrealizedPl.toFixed(2)}
                  </td>
                  <td className={`px-4 py-4 text-right font-bold ${
                    pos.unrealizedPlpc >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}>
                    {(pos.unrealizedPlpc * 100).toFixed(2)}%
                  </td>
                  <td className="px-4 py-4 text-right text-slate-300">
                    ${pos.marketValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-4 py-4 text-right text-slate-400">
                    {typeof pos.takeProfit === 'number' ? `$${pos.takeProfit.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-4 text-right text-slate-400">
                    {typeof pos.stopLoss === 'number' ? `$${pos.stopLoss.toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-4 text-center">
                    <button 
                      onClick={() => closePosition(pos.id)} 
                      className="text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 p-1.5 rounded-lg transition-all" 
                      aria-label={`Close position for ${pos.symbol}`}
                    >
                      <MinusCircleIcon className="w-5 h-5" />
                    </button>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={9} className="text-center py-12 text-slate-500">
                    <div className="flex flex-col items-center gap-2">
                      <span className="text-2xl">📊</span>
                      <span>No open positions</span>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
