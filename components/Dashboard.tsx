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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6">
      <div className="max-w-[1920px] mx-auto space-y-6">
        {/* Connection Status Alerts */}
        {!isConnected && (
          <div className="bg-red-500/10 backdrop-blur-sm border border-red-500/30 rounded-xl p-4 shadow-lg">
            <p className="text-red-400 font-semibold flex items-center gap-2">
              <span className="text-lg">⚠️</span> Backend Disconnected
            </p>
            <p className="text-red-300/80 text-sm mt-1">
              {error || "Unable to connect to trading backend"}
            </p>
          </div>
        )}
        {streamingStatus !== "connected" && (
          <div
            className={`backdrop-blur-sm rounded-xl p-4 border shadow-lg ${
              streamingStatus === "error"
                ? "bg-orange-500/10 border-orange-500/30"
                : "bg-yellow-500/10 border-yellow-500/30"
            }`}
          >
            <p className="text-sm font-semibold text-yellow-400 flex items-center gap-2">
              {streamingStatus === "connecting" && (
                <>
                  <span className="animate-pulse">⚡</span> Establishing real-time stream…
                </>
              )}
              {streamingStatus === "disabled" && (
                <>
                  <span>⚠️</span> Streaming disabled. Using 10s polling fallback.
                </>
              )}
              {streamingStatus === "error" && (
                <>
                  <span>⚠️</span> Streaming unavailable. Falling back to polling.
                </>
              )}
            </p>
          </div>
        )}

        {/* KPI Cards - Improved spacing and layout */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
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

        {/* Main Content - Two Column Layout */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Left Column - Trading Data (2/3 width) */}
          <div className="xl:col-span-2 space-y-6">
            <SimpleChart data={performanceData} />
            <PositionsTable positions={positions} closePosition={closePosition} />
            <OrdersTable orders={orders} cancelOrder={cancelOrder} />
          </div>

          {/* Right Column - Interactive Panels (1/3 width) */}
          <div className="flex flex-col gap-6">
            <ChatPanel />
            <AdvisoryPanel advisories={advisories} />
          </div>
        </div>

        {/* Bottom Section - Analysis & Logs */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Trade Analysis (2/3 width) */}
          <div className="xl:col-span-2">
            <TradeAnalysisLog analyses={tradeAnalyses} />
          </div>

          {/* Right Column - Status & Logs (1/3 width) */}
          <div className="flex flex-col gap-6">
            <ReadinessChecklist />
            <LogFeed logs={logs} />
          </div>
        </div>
      </div>
    </div>
  );
};
