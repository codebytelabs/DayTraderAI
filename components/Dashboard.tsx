
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
    isConnected,
    error,
  } = useTrading();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {/* Connection Status */}
      {!isConnected && (
        <div className="lg:col-span-3 xl:col-span-4 bg-red-900/20 border border-red-500 rounded-lg p-4">
          <p className="text-red-400 font-semibold">⚠️ Backend Disconnected</p>
          <p className="text-red-300 text-sm">{error || 'Unable to connect to trading backend'}</p>
        </div>
      )}
      
      {/* KPIs */}
      <div className="lg:col-span-3 xl:col-span-4 grid grid-cols-2 md:grid-cols-4 gap-6">
        <StatCard title="Today's P/L" value={stats.daily_pl.toLocaleString('en-US', { style: 'currency', currency: 'USD' })} change={`${stats.daily_pl_pct.toFixed(2)}%`} isPositive={stats.daily_pl >= 0} />
        <StatCard title="Win Rate" value={`${(stats.win_rate * 100).toFixed(1)}%`} change={`${stats.wins}W / ${stats.losses}L`} isPositive={stats.win_rate >= 0.5} />
        <StatCard title="Profit Factor" value={stats.profit_factor.toFixed(2)} isPositive={stats.profit_factor >= 1} />
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
