
import React from 'react';
import { StatCard } from './StatCard';
import { PositionsTable } from './PositionsTable';
import { OrdersTable } from './OrdersTable';
import { PerformanceChart } from './PerformanceChart';
import { ReadinessChecklist } from './ReadinessChecklist';
import { LogFeed } from './LogFeed';
import { AdvisoryPanel } from './AdvisoryPanel';
import { ChatPanel } from './ChatPanel';
import { useTrading } from '../state/TradingContext';
import { TradeAnalysisLog } from './TradeAnalysisLog';

export const Dashboard: React.FC = () => {
  const {
    stats,
    performanceData,
    positions,
    orders,
    logs,
    advisories,
    tradeAnalyses,
    closePosition,
    cancelOrder,
  } = useTrading();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {/* KPIs */}
      <div className="lg:col-span-3 xl:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-6">
        <StatCard title="Today's P/L" value={stats.dailyPl.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} change={`${stats.dailyPlPc.toFixed(2)}%`} isPositive={stats.dailyPl >= 0} />
        <StatCard title="Win Rate" value={`${(stats.winRate * 100).toFixed(1)}%`} change={`${stats.wins}W / ${stats.losses}L`} isPositive={stats.winRate >= 0.5} />
        <StatCard title="Profit Factor" value={stats.profitFactor.toFixed(2)} isPositive={stats.profitFactor >= 1} />
        <StatCard title="Open Positions" value={positions.length.toString()} isPositive={true} />
      </div>

      {/* Main Content Area */}
      <div className="lg:col-span-3 xl:col-span-3 flex flex-col gap-6">
        <PerformanceChart data={performanceData} />
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <PositionsTable positions={positions} closePosition={closePosition} />
          <OrdersTable orders={orders} cancelOrder={cancelOrder} />
        </div>
        <TradeAnalysisLog analyses={tradeAnalyses} />
      </div>

      {/* Right Sidebar */}
      <div className="lg:col-span-3 xl:col-span-1 flex flex-col gap-6">
        <ChatPanel />
        <AdvisoryPanel advisories={advisories} />
        <ReadinessChecklist />
        <LogFeed logs={logs} />
      </div>
    </div>
  );
};
