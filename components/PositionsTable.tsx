
import React from 'react';
import { Position, OrderSide } from '../types';
import { MinusCircleIcon } from './icons/MinusCircleIcon';

interface PositionsTableProps {
  positions: Position[];
  closePosition: (positionId: string) => void;
}

export const PositionsTable: React.FC<PositionsTableProps> = ({ positions, closePosition }) => {
  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2 overflow-x-auto">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Open Positions ({positions.length})</h3>
      <div className="max-h-[300px] overflow-y-auto">
        <table className="w-full text-sm text-left">
          <thead className="text-xs text-brand-text-secondary uppercase border-b border-brand-surface-2 sticky top-0 bg-brand-surface">
            <tr>
              <th scope="col" className="px-4 py-3">Symbol</th>
              <th scope="col" className="px-4 py-3">Side</th>
              <th scope="col" className="px-4 py-3">Qty</th>
              <th scope="col" className="px-4 py-3">P/L ($)</th>
              <th scope="col" className="px-4 py-3">P/L (%)</th>
              <th scope="col" className="px-4 py-3">Market Value</th>
              <th scope="col" className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {positions.length > 0 ? positions.map((pos) => (
              <tr key={pos.id} className="hover:bg-brand-surface-2 border-b border-brand-surface-2">
                <td className="px-4 py-3 font-medium">{pos.symbol}</td>
                <td className={`px-4 py-3 font-semibold ${pos.side === OrderSide.BUY ? 'text-brand-success' : 'text-brand-danger'}`}>
                  {pos.side === OrderSide.BUY ? 'LONG' : 'SHORT'}
                </td>
                <td className="px-4 py-3">{pos.qty}</td>
                <td className={`px-4 py-3 font-semibold ${pos.unrealizedPl >= 0 ? 'text-brand-success' : 'text-brand-danger'}`}>
                  {pos.unrealizedPl.toFixed(2)}
                </td>
                <td className={`px-4 py-3 font-semibold ${pos.unrealizedPlpc >= 0 ? 'text-brand-success' : 'text-brand-danger'}`}>
                  {(pos.unrealizedPlpc * 100).toFixed(2)}%
                </td>
                <td className="px-4 py-3">${pos.marketValue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td className="px-4 py-3">
                  <button onClick={() => closePosition(pos.id)} className="text-brand-danger hover:text-red-400 transition-colors" aria-label={`Close position for ${pos.symbol}`}>
                    <MinusCircleIcon className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            )) : (
              <tr>
                <td colSpan={7} className="text-center py-4 text-brand-text-secondary">No open positions.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
