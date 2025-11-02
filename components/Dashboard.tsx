import React from "react";
import { StatCard } from "./StatCard";
import { PositionsTable } from "./PositionsTable";
import { OrdersTable } from "./OrdersTable";
import { SimpleChart } from "./SimpleChart";
import { ReadinessChecklist } from "./ReadinessChecklist";
import { LogFeed } from "./LogFeed";
import { AdvisoryPanel } from "./AdvisoryPanel";
import { ChatPanel } from "./ChatPanel";
import { useTrading } from "../state/TradingContext";
import { TradeAnalysisLog } from "./TradeAnalysisLog";

export const Dashboard: React.FC = () => {
  const {
    stats,
    performanceData,
    positions,
    orders,
    logs,
    advisories,
    tradeAnalyses,
    timeframe,
    setTimeframe,
    closePosition,
    cancelOrder,
    isConnected,
    error,
    streamingStatus,
  } = useTrading();

  return (
    <div className="grid grid-cols-12 gap-5">
      {/* Connection Status */}
      {!isConnected && (
        <div className="col-span-12 bg-red-900/20 border border-red-500 rounded-lg p-4">
          <p className="text-red-400 font-semibold">⚠️ Backend Disconnected</p>
          <p className="text-red-300 text-sm">
            {error || "Unable to connect to trading backend"}
          </p>
        </div>
      )}
      {streamingStatus !== "connected" && (
        <div
          className={`col-span-12 rounded-lg p-4 border ${
            streamingStatus === "error"
              ? "bg-orange-900/20 border-orange-500"
              : "bg-yellow-900/20 border-yellow-500"
          }`}
        >
          <p className="text-sm font-semibold text-brand-warning">
            {streamingStatus === "connecting" &&
              "⚡ Establishing real-time stream…"}
            {streamingStatus === "disabled" &&
              "⚠️ Streaming disabled. Using 10s polling fallback."}
            {streamingStatus === "error" &&
              "⚠️ Streaming unavailable. Falling back to polling."}
          </p>
        </div>
      )}

      {/* KPIs */}
      <div className="col-span-12 grid grid-cols-2 md:grid-cols-4 2xl:grid-cols-6 gap-6">
        <StatCard
          title="Today's P/L"
          value={stats.daily_pl.toLocaleString("en-US", {
            style: "currency",
            currency: "USD",
          })}
          change={`${stats.daily_pl_pct.toFixed(2)}%`}
          isPositive={stats.daily_pl >= 0}
        />
        <StatCard
          title="Win Rate"
          value={`${(stats.win_rate * 100).toFixed(1)}%`}
          change={`${stats.wins}W / ${stats.losses}L`}
          isPositive={stats.win_rate >= 0.5}
        />
        <StatCard
          title="Profit Factor"
          value={stats.profit_factor.toFixed(2)}
          isPositive={stats.profit_factor >= 1}
        />
        <StatCard
          title="Open Positions"
          value={positions.length.toString()}
          isPositive={true}
        />
      </div>

      {/* Main Content Row */}
      <div className="col-span-12 grid grid-cols-1 xl:grid-cols-12 gap-6">
        <div className="xl:col-span-8 flex flex-col gap-6">
          <SimpleChart data={performanceData} />
          <PositionsTable positions={positions} closePosition={closePosition} />
          <OrdersTable orders={orders} cancelOrder={cancelOrder} />
        </div>
        <div className="xl:col-span-4 flex flex-col gap-6">
          <ChatPanel />
          <div className="max-h-96 overflow-y-auto">
            <AdvisoryPanel advisories={advisories} />
          </div>
        </div>
      </div>

      {/* Analysis Row */}
      <div className="col-span-12 grid grid-cols-1 xl:grid-cols-12 gap-6 mt-6">
        <div className="xl:col-span-8 max-h-96 overflow-y-auto">
          <TradeAnalysisLog analyses={tradeAnalyses} />
        </div>
        <div className="xl:col-span-4 flex flex-col gap-6">
          <ReadinessChecklist />
          <div className="flex-1 min-h-0 overflow-y-auto">
            <LogFeed logs={logs} />
          </div>
        </div>
      </div>
    </div>
  );
};
