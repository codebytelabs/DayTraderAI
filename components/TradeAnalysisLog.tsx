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
    return [...analyses].reverse().slice(0, 10);
  }, [analyses]);

  if (entries.length === 0) {
    return (
      <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
        <div className="flex items-center gap-2 mb-5">
          <span className="text-xl">🧠</span>
          <h3 className="text-xl font-bold text-white">Trade Analysis & Rationale</h3>
        </div>
        <div className="text-center py-16 text-slate-500">
          <div className="flex flex-col items-center gap-3">
            <span className="text-4xl">🔍</span>
            <span>Awaiting first trade signal for AI analysis...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">🧠</span>
        <h3 className="text-xl font-bold text-white">Trade Analysis & Rationale</h3>
      </div>
      <div className="space-y-4 max-h-[500px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {entries.map((analysis) => {
          const isLong = analysis.side === OrderSide.BUY;
          const borderClass = isLong ? 'border-l-emerald-500' : 'border-l-rose-500';
          const headingColor = isLong ? 'text-emerald-400' : 'text-rose-400';

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
                ? 'text-emerald-400'
                : 'text-rose-400'
              : 'text-white';
          const pnlPctTone =
            typeof analysis.pnlPct === 'number'
              ? analysis.pnlPct >= 0
                ? 'text-emerald-400'
                : 'text-rose-400'
              : isLong
                ? 'text-emerald-400'
                : 'text-rose-400';

          return (
            <div key={analysis.id} className={`text-sm p-4 bg-slate-900/50 rounded-lg border-l-4 ${borderClass} hover:bg-slate-900/70 transition-all`}>
              <div className="flex justify-between items-start mb-3 gap-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`font-bold text-base ${headingColor}`}>
                    {isLong ? 'LONG' : 'SHORT'}
                  </span>
                  <span className="font-bold text-base text-white">{analysis.symbol}</span>
                  {actionLabel && (
                    <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-xs uppercase text-slate-400 font-semibold">
                      {actionLabel}
                    </span>
                  )}
                </div>
                <span className="text-xs text-slate-500 flex-shrink-0">
                  {new Date(analysis.timestamp).toLocaleTimeString()}
                </span>
              </div>

              <p className="text-slate-300 mb-4 leading-relaxed whitespace-pre-line">
                <span className="font-semibold text-blue-400">[{sourceLabel}] </span>
                {analysis.analysis}
              </p>

              {(pnl || pnlPct || entry || target || stop) && (
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs border-t border-slate-800 pt-3">
                  {pnl && (
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-slate-500 mb-1">P/L</p>
                      <p className={`font-mono font-bold ${pnlTone}`}>{pnl}</p>
                    </div>
                  )}
                  {pnlPct && (
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-slate-500 mb-1">P/L %</p>
                      <p className={`font-mono font-bold ${pnlPctTone}`}>{pnlPct}</p>
                    </div>
                  )}
                  {entry && (
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-slate-500 mb-1">Entry</p>
                      <p className="font-mono text-white">{entry}</p>
                    </div>
                  )}
                  {target && (
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-slate-500 mb-1">Target</p>
                      <p className="font-mono text-emerald-400">{target}</p>
                    </div>
                  )}
                  {stop && (
                    <div className="bg-slate-800/50 p-2 rounded">
                      <p className="text-slate-500 mb-1">Stop</p>
                      <p className="font-mono text-rose-400">{stop}</p>
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
