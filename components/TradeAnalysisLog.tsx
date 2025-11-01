import React from 'react';
import { TradeAnalysis, OrderSide } from '../types';

export const TradeAnalysisLog: React.FC<{ analyses: TradeAnalysis[] }> = ({ analyses }) => {
  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Trade Analysis & Rationale</h3>
      <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
        {analyses.length > 0 ? analyses.map((analysis) => (
          <div key={analysis.id} className="text-sm p-3 bg-brand-surface-2 rounded-md border-l-4
            ${analysis.side === OrderSide.BUY ? 'border-brand-success' : 'border-brand-danger'}">
            
            <div className="flex justify-between items-center mb-2">
              <div>
                <span className={`font-bold text-lg ${analysis.side === OrderSide.BUY ? 'text-brand-success' : 'text-brand-danger'}`}>
                  {analysis.side === OrderSide.BUY ? 'LONG' : 'SHORT'}
                </span>
                <span className="font-bold text-lg text-brand-text ml-2">{analysis.symbol}</span>
              </div>
              <span className="text-xs text-brand-text-secondary">
                {new Date(analysis.timestamp).toLocaleTimeString()}
              </span>
            </div>

            <p className="text-brand-text mb-3">
              <span className="font-bold text-blue-400">[{analysis.source} Analysis] </span>
              {analysis.reasoning}
            </p>
            
            <div className="grid grid-cols-3 gap-2 text-center text-xs border-t border-brand-surface pt-2">
                <div>
                    <p className="text-brand-text-secondary">Entry</p>
                    <p className="font-mono text-brand-text">${analysis.entryPrice.toFixed(2)}</p>
                </div>
                 <div>
                    <p className="text-brand-text-secondary">Target</p>
                    <p className="font-mono text-brand-success">${analysis.takeProfit.toFixed(2)}</p>
                </div>
                 <div>
                    <p className="text-brand-text-secondary">Stop Loss</p>
                    <p className="font-mono text-brand-danger">${analysis.stopLoss.toFixed(2)}</p>
                </div>
            </div>
          </div>
        )) : (
          <div className="text-center py-10 text-brand-text-secondary text-sm">Awaiting first trade signal for AI analysis...</div>
        )}
      </div>
    </div>
  );
};