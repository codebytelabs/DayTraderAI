import { motion } from 'framer-motion';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';

interface TradingChartProps {
  data: { time: number; value: number }[];
  height?: number;
  type?: 'area' | 'line';
  timeframe?: '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';
  colors?: {
    line?: string;
    areaTop?: string;
    areaBottom?: string;
  };
}

// Format time based on timeframe
const formatTimeForTimeframe = (timestamp: number, timeframe: string): string => {
  const date = new Date(timestamp * 1000);
  
  switch (timeframe) {
    case '1D':
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    case '1W':
      return date.toLocaleDateString([], { weekday: 'short', hour: '2-digit' });
    case '1M':
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    case '3M':
    case '1Y':
    case 'ALL':
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
    default:
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
};

export function TradingChart({
  data,
  height = 300,
  timeframe = '1D',
  colors = {},
}: TradingChartProps) {
  const {
    line = '#3b82f6',
    areaTop = 'rgba(59, 130, 246, 0.4)',
    areaBottom = 'rgba(59, 130, 246, 0)',
  } = colors;

  const gradientId = `chart-gradient-${Math.random().toString(36).slice(2, 11)}`;

  const formattedData = data.map((d) => ({
    time: d.time,
    value: d.value,
    formattedTime: formatTimeForTimeframe(d.time, timeframe),
  }));

  return (
    <motion.div
      className="w-full"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      style={{ height }}
    >
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={areaTop} stopOpacity={1} />
              <stop offset="100%" stopColor={areaBottom} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="rgba(255, 255, 255, 0.03)"
            vertical={false}
          />
          <XAxis
            dataKey="formattedTime"
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            stroke="#64748b"
            tick={{ fontSize: 11, fill: '#64748b' }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value) => `$${value.toLocaleString()}`}
            domain={['auto', 'auto']}
            width={80}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(17, 24, 39, 0.95)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
              padding: '12px 16px',
            }}
            itemStyle={{ color: '#f8fafc', fontSize: '14px', fontWeight: 500 }}
            labelStyle={{ color: '#94a3b8', fontSize: '12px', marginBottom: '4px' }}
            formatter={(value: number) => [`$${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`, 'Value']}
            labelFormatter={(label) => label}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={line}
            strokeWidth={2}
            fill={`url(#${gradientId})`}
            animationDuration={1000}
            animationEasing="ease-out"
          />
        </AreaChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

interface MiniSparklineProps {
  data: number[];
  width?: number;
  height?: number;
  positive?: boolean;
}

export function MiniSparkline({
  data,
  width = 80,
  height = 32,
  positive = true,
}: MiniSparklineProps) {
  if (data.length < 2) return null;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  const gradientId = `sparkline-${Math.random().toString(36).slice(2, 11)}`;
  const strokeColor = positive ? '#10b981' : '#ef4444';
  const fillColor = positive ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';

  return (
    <svg width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={fillColor} />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <polygon
        points={`0,${height} ${points} ${width},${height}`}
        fill={`url(#${gradientId})`}
      />
      <polyline
        points={points}
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
