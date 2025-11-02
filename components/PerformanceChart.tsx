import React from "react";
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  TooltipProps,
  ReferenceLine,
} from "recharts";
import { PerformanceDataPoint } from "../types";

interface PerformanceChartProps {
  data: PerformanceDataPoint[];
  onTimeframeChange?: (timeframe: string) => void;
  selectedTimeframe?: string;
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    // The payload can be from either line, find one with the full data object
    const dataPayload = payload.find((p: any) => p.payload);
    if (!dataPayload) return null;

    const data = dataPayload.payload as PerformanceDataPoint;
    const pnlColor = data.pnl >= 0 ? "text-brand-success" : "text-brand-danger";
    const candleColor =
      data.close >= data.open ? "text-brand-success" : "text-brand-danger";

    return (
      <div className="bg-brand-surface-2 p-3 rounded-lg border border-brand-accent text-sm shadow-xl">
        <p className="font-bold text-brand-text mb-2">
          Time: {new Date(data.timestamp).toLocaleTimeString()}
        </p>
        <div className="space-y-1 font-mono">
          <div className="flex justify-between items-center gap-4">
            <span className="text-brand-text-secondary">Open:</span>
            <span className="font-semibold text-brand-text">
              {data.open.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">High:</span>
            <span className="font-semibold text-brand-text">
              {data.high.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">Low:</span>
            <span className="font-semibold text-brand-text">
              {data.low.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">Close:</span>
            <span className={`font-semibold ${candleColor}`}>
              {data.close.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            </span>
          </div>
          <hr className="border-brand-surface" />
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">P/L:</span>
            <span className={`font-semibold ${pnlColor}`}>
              {data.pnl.toLocaleString("en-US", {
                style: "currency",
                currency: "USD",
              })}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">Win Rate:</span>
            <span className={`font-semibold`}>
              {(data.winRate * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-brand-text-secondary">Profit Factor:</span>
            <span className={`font-semibold`}>
              {data.profitFactor.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return null;
};

// Simple line chart instead of candlesticks for now
// Candlesticks require complex coordinate transformation

const CustomizedAxisTick = (props: any) => {
  const { x, y, payload } = props;
  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        dy={16}
        textAnchor="end"
        fill="#A3A3C2"
        fontSize={12}
        transform="rotate(-35)"
      >
        {new Date(payload.value).toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })}
      </text>
    </g>
  );
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({
  data,
  onTimeframeChange,
  selectedTimeframe = "1D",
}) => {
  console.log("[PerformanceChart] Received data:", {
    dataLength: data.length,
    firstPoint: data[0],
    lastPoint: data[data.length - 1],
    allData: data,
  });

  const yDomain =
    data.length > 0
      ? [
          Math.min(...data.map((d) => d.low)) * 0.995,
          Math.max(...data.map((d) => d.high)) * 1.005,
        ]
      : [0, 1];

  const timeframes = ["1D"]; // Only 1D works for accounts > 30 days old

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2 h-96">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-brand-text">
          Portfolio Equity Curve
        </h3>
        {onTimeframeChange && (
          <div className="flex gap-2">
            {timeframes.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(tf)}
                className={`px-3 py-1 text-sm font-medium rounded transition ${
                  selectedTimeframe === tf
                    ? "bg-brand-accent text-white"
                    : "bg-brand-surface-2 text-brand-text-secondary hover:bg-brand-surface hover:text-brand-text"
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        )}
      </div>
      {data.length === 0 ? (
        <div className="flex items-center justify-center h-[calc(100%-40px)] text-brand-text-secondary">
          <p>
            No performance data available yet. Waiting for portfolio history...
          </p>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="calc(100% - 40px)">
          <ComposedChart
            data={data}
            margin={{ top: 5, right: 20, left: 10, bottom: 40 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#2A2C3F" />
            <XAxis
              dataKey="timestamp"
              stroke="#A3A3C2"
              tick={<CustomizedAxisTick />}
              interval="preserveStartEnd"
            />
            <YAxis
              stroke="#A3A3C2"
              tick={{ fontSize: 12 }}
              domain={yDomain}
              tickFormatter={(value) =>
                `$${Number(value).toLocaleString(undefined, {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                })}`
              }
              orientation="right"
              axisLine={false}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            {data.length > 0 && (
              <ReferenceLine
                y={data[0]?.open}
                label={{
                  value: "Initial Equity",
                  position: "insideTopLeft",
                  fill: "#A3A3C2",
                }}
                stroke="#A3A3C2"
                strokeDasharray="4 4"
              />
            )}

            {/* Line chart for equity curve */}
            <Line
              dataKey="close"
              stroke="#059669"
              strokeWidth={2}
              dot={false}
              type="monotone"
            />
          </ComposedChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
