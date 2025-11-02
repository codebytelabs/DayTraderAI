import React, { useMemo } from 'react';
import { TradeAnalysis, OrderSide } from '../types';

interface TradeAnalysisLogProps {
  analyses: TradeAnalysis[];
}

const formatCurrency = (value?: number) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' });
};

const formatPercent = (value?: number) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return null;
  }
  return `${value.toFixed(2)}%`;
};

export const TradeAnalysisLog: React.FC<TradeAnalysisLogProps> = ({ analyses }) => {
  const entries = useMemo(() => {
    console.log('[TradeAnalysisLog] Received analyses:', analyses.length);
    // Show the most recent analyses first to keep the list readable.
    return [...analyses].reverse().slice(0, 10);
  }, [analyses]);

  if (entries.length === 0) {
    return (
      <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
        <h3 className="text-lg font-semibold text-brand-text mb-4">Trade Analysis &amp; Rationale</h3>
        <div className="text-center py-6 text-brand-text-secondary text-sm">
          Awaiting first trade signal for AI analysis...
        </div>
      </div>
    );
  }

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Trade Analysis &amp; Rationale</h3>
      <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
        {entries.map((analysis) => {
          const isLong = analysis.side === OrderSide.BUY;
          const borderClass = isLong ? 'border-brand-success' : 'border-brand-danger';
          const headingColor = isLong ? 'text-brand-success' : 'text-brand-danger';

          const pnl = formatCurrency(analysis.pnl);
          const pnlPct = formatPercent(analysis.pnlPct);
          const entry = formatCurrency(analysis.entryPrice);
          const target = formatCurrency(analysis.takeProfit);
          const stop = formatCurrency(analysis.stopLoss);
          const sourceLabel = analysis.source ?? 'AI';
          const actionLabel = analysis.action ? analysis.action.toUpperCase() : null;
          const pnlTone =
            typeof analysis.pnl === 'number'
              ? analysis.pnl >= 0
                ? 'text-brand-success'
                : 'text-brand-danger'
              : 'text-brand-text';
          const pnlPctTone =
            typeof analysis.pnlPct === 'number'
              ? analysis.pnlPct >= 0
                ? 'text-brand-success'
                : 'text-brand-danger'
              : isLong
                ? 'text-brand-success'
                : 'text-brand-danger';

          return (
            <div key={analysis.id} className={`text-sm p-3 bg-brand-surface-2 rounded-md border-l-4 ${borderClass}`}>
              <div className="flex justify-between items-start mb-2 gap-2">
                <div>
                  <span className={`font-bold text-lg ${headingColor}`}>
                    {isLong ? 'LONG' : 'SHORT'}
                  </span>
                  <span className="font-bold text-lg text-brand-text ml-2">{analysis.symbol}</span>
                  {actionLabel && (
                    <span className="ml-2 px-2 py-0.5 rounded-full bg-brand-surface text-xs uppercase text-brand-text-secondary">
                      {actionLabel}
                    </span>
                  )}
                </div>
                <span className="text-xs text-brand-text-secondary">
                  {new Date(analysis.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <p className="text-brand-text mb-3 whitespace-pre-line">
                <span className="font-semibold text-blue-400">[{sourceLabel}] </span>
                {analysis.analysis}
              </p>

              {(pnl || pnlPct || entry || target || stop) && (
                <div className="flex flex-wrap gap-3 text-xs border-t border-brand-surface pt-2">
                  {pnl && (
                    <div>
                      <p className="text-brand-text-secondary">P/L</p>
                      <p className={`font-mono ${pnlTone}`}>{pnl}</p>
                    </div>
                  )}
                  {pnlPct && (
                    <div>
                      <p className="text-brand-text-secondary">P/L %</p>
                      <p className={`font-mono ${pnlPctTone}`}>{pnlPct}</p>
                    </div>
                  )}
                  {entry && (
                    <div>
                      <p className="text-brand-text-secondary">Entry</p>
                      <p className="font-mono text-brand-text">{entry}</p>
                    </div>
                  )}
                  {target && (
                    <div>
                      <p className="text-brand-text-secondary">Target</p>
                      <p className="font-mono text-brand-success">{target}</p>
                    </div>
                  )}
                  {stop && (
                    <div>
                      <p className="text-brand-text-secondary">Stop</p>
                      <p className="font-mono text-brand-danger">{stop}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
