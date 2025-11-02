import React, { useMemo } from 'react';
import { ChecklistItem, ChecklistStatus, PerformanceDataPoint } from '../types';
import { useTrading } from '../state/TradingContext';
import { CheckCircleIcon } from './icons/CheckCircleIcon';
import { XCircleIcon } from './icons/XCircleIcon';
import { ClockIcon } from './icons/ClockIcon';

const StatusIcon: React.FC<{ status: ChecklistStatus }> = ({ status }) => {
  switch (status) {
    case ChecklistStatus.PASS:
      return <CheckCircleIcon className="w-5 h-5 text-emerald-400" />;
    case ChecklistStatus.FAIL:
      return <XCircleIcon className="w-5 h-5 text-rose-400" />;
    case ChecklistStatus.PENDING:
      return <ClockIcon className="w-5 h-5 text-yellow-400" />;
    default:
      return null;
  }
};

export const ReadinessChecklist: React.FC = () => {
  const { stats, performanceData, positions, riskSettings } = useTrading();

  const checklist: ChecklistItem[] = useMemo(() => {
    const totalTrades = stats.wins + stats.losses;
    const winRatePct = stats.win_rate * 100;
    const profitFactor = stats.profit_factor;
    const maxDrawdown = calculateMaxDrawdown(performanceData);

    const performance: ChecklistItem = {
      category: 'Performance',
      items: [
        {
          name: 'Trades ≥ 300',
          status: totalTrades >= 300 ? ChecklistStatus.PASS : ChecklistStatus.PENDING,
          details: `${totalTrades}/300 trades`,
        },
        {
          name: 'Win Rate ≥ 60%',
          status: winRatePct >= 60 ? ChecklistStatus.PASS : ChecklistStatus.PENDING,
          details: `${winRatePct.toFixed(1)}%`,
        },
        {
          name: 'Profit Factor ≥ 1.5',
          status: profitFactor >= 1.5 ? ChecklistStatus.PASS : ChecklistStatus.FAIL,
          details: profitFactor.toFixed(2),
        },
        {
          name: 'Max Drawdown ≤ 15%',
          status: maxDrawdown <= 0.15 ? ChecklistStatus.PASS : ChecklistStatus.FAIL,
          details: `${(maxDrawdown * 100).toFixed(2)}%`,
        },
      ],
    };

    const execution: ChecklistItem = {
      category: 'Execution & Data',
      items: [
        {
          name: 'Slippage Within Budget',
          status: ChecklistStatus.PENDING,
          details: 'Awaiting live execution metrics',
        },
        {
          name: 'Fill Rate ≥ 95%',
          status: ChecklistStatus.PENDING,
          details: 'Paper fills simulated at 100%',
        },
        {
          name: 'No Critical Data Gaps',
          status: ChecklistStatus.PASS,
          details: 'Streaming simulation stable',
        },
      ],
    };

    const ops: ChecklistItem = {
      category: 'Operations & Risk',
      items: [
        {
          name: 'Max Positions Observed',
          status:
            positions.length <= riskSettings.maxPositions ? ChecklistStatus.PASS : ChecklistStatus.FAIL,
          details: `${positions.length}/${riskSettings.maxPositions}`,
        },
        {
          name: 'Circuit Breakers Tested',
          status: ChecklistStatus.PENDING,
          details: 'Run incident drill',
        },
        {
          name: 'Emergency Runbooks Ready',
          status: ChecklistStatus.PENDING,
          details: 'Document incident response',
        },
        {
          name: 'Recovery Drills Passed',
          status: ChecklistStatus.PENDING,
          details: 'Schedule recovery dry-run',
        },
      ],
    };

    return [performance, execution, ops];
  }, [stats, performanceData, positions, riskSettings]);

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">✅</span>
        <h3 className="text-xl font-bold text-white">Paper → Live Readiness</h3>
      </div>
      <div className="space-y-5">
        {checklist.map((categoryItem) => (
          <div key={categoryItem.category}>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
              {categoryItem.category}
            </h4>
            <ul className="space-y-2.5">
              {categoryItem.items.map((item) => (
                <li key={item.name} className="flex items-start justify-between text-sm bg-slate-900/30 p-3 rounded-lg border border-slate-800/50">
                  <div className="flex items-center gap-2">
                    <StatusIcon status={item.status} />
                    <span className="text-slate-200 font-medium">{item.name}</span>
                  </div>
                  <span className="text-xs text-slate-400 text-right ml-3 font-mono">{item.details}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

function calculateMaxDrawdown(data: PerformanceDataPoint[]): number {
  if (!data.length) return 0;
  let peak = data[0].close;
  let maxDrawdown = 0;
  for (const point of data) {
    peak = Math.max(peak, point.close);
    const drawdown = peak > 0 ? (peak - point.close) / peak : 0;
    maxDrawdown = Math.max(maxDrawdown, drawdown);
  }
  return maxDrawdown;
}
