import { useState, useMemo, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Loader2 } from 'lucide-react';
import { PremiumCard } from './ui/PremiumCard';
import { TradingChart } from './ui/TradingChart';
import { ChartSkeleton } from './ui/LoadingStates';
import { AnimatedCurrency, AnimatedPercent } from './ui/AnimatedNumber';
import type { PortfolioHistoryPoint } from '../hooks/useMarketData';

interface PortfolioChartProps {
    data: PortfolioHistoryPoint[];
}

type TimeRange = '1D' | '1W' | '1M' | '3M' | '1Y' | 'ALL';

const API_BASE_URL = 'http://localhost:8006';

export function PortfolioChart({ data }: PortfolioChartProps) {
    const [selectedRange, setSelectedRange] = useState<TimeRange>('1D');
    const [chartData, setChartData] = useState<PortfolioHistoryPoint[]>(data);
    const [isLoadingTimeframe, setIsLoadingTimeframe] = useState(false);

    const timeRanges: TimeRange[] = ['1D', '1W', '1M', '3M', '1Y', 'ALL'];

    // Fetch data for selected timeframe
    const fetchTimeframeData = useCallback(async (timeframe: TimeRange) => {
        setIsLoadingTimeframe(true);
        try {
            const response = await fetch(`${API_BASE_URL}/performance?timeframe=${timeframe}`);
            if (response.ok) {
                const newData = await response.json();
                if (Array.isArray(newData) && newData.length > 0) {
                    setChartData(newData);
                }
            }
        } catch (error) {
            console.error('Failed to fetch timeframe data:', error);
        } finally {
            setIsLoadingTimeframe(false);
        }
    }, []);

    // Only update chart data from props when on 1D timeframe (default polling data)
    useEffect(() => {
        if (data && data.length > 0 && selectedRange === '1D') {
            setChartData(data);
        }
    }, [data, selectedRange]);

    // Handle timeframe change
    const handleTimeframeChange = (range: TimeRange) => {
        if (range !== selectedRange) {
            setSelectedRange(range);
            fetchTimeframeData(range);
        }
    };

    // Transform data for chart
    const filteredData = useMemo(() => {
        if (!chartData || chartData.length === 0) return [];
        return chartData.map(d => ({ time: d.timestamp, value: d.equity }));
    }, [chartData]);

    // Calculate stats
    const stats = useMemo(() => {
        if (filteredData.length < 2) {
            return { change: 0, changePercent: 0, high: 0, low: 0, current: 0 };
        }
        
        const values = filteredData.map(d => d.value);
        const first = values[0];
        const last = values[values.length - 1];
        const change = last - first;
        const changePercent = first > 0 ? (change / first) * 100 : 0;
        
        return {
            change,
            changePercent,
            high: Math.max(...values),
            low: Math.min(...values),
            current: last,
        };
    }, [filteredData]);

    const isPositive = stats.change >= 0;

    if (!data || data.length === 0) {
        return <ChartSkeleton height={350} />;
    }

    return (
        <PremiumCard className="p-0 overflow-hidden">
            {/* Header */}
            <div className="p-6 pb-0">
                <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
                    <div>
                        <h2 className="text-lg font-semibold text-white mb-1">Portfolio Performance</h2>
                        <p className="text-sm text-text-secondary">Net Liquidation Value</p>
                        
                        <div className="mt-4 flex items-end gap-4">
                            <div>
                                <p className="text-3xl font-bold text-white metric-value">
                                    <AnimatedCurrency value={stats.current} />
                                </p>
                            </div>
                            <div className={`flex items-center gap-2 pb-1 ${isPositive ? 'text-success' : 'text-danger'}`}>
                                {isPositive ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                                <span className="font-semibold">
                                    <AnimatedCurrency value={stats.change} showSign />
                                </span>
                                <span className="text-sm">
                                    (<AnimatedPercent value={stats.changePercent} />)
                                </span>
                            </div>
                        </div>
                    </div>

                    {/* Time Range Selector */}
                    <div className="flex items-center gap-1 p-1 bg-surface rounded-xl">
                        {timeRanges.map((range) => (
                            <motion.button
                                key={range}
                                onClick={() => handleTimeframeChange(range)}
                                disabled={isLoadingTimeframe}
                                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50 ${
                                    selectedRange === range
                                        ? 'bg-primary text-white shadow-lg shadow-primary/25'
                                        : 'text-text-secondary hover:text-white hover:bg-surface-elevated'
                                }`}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                            >
                                {isLoadingTimeframe && selectedRange === range ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    range
                                )}
                            </motion.button>
                        ))}
                    </div>
                </div>

                {/* Stats Row */}
                <div className="flex items-center gap-8 mb-4">
                    <div>
                        <p className="text-xs text-text-muted mb-1">High</p>
                        <p className="text-sm font-semibold text-success">
                            ${stats.high.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-text-muted mb-1">Low</p>
                        <p className="text-sm font-semibold text-danger">
                            ${stats.low.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </p>
                    </div>
                    <div>
                        <p className="text-xs text-text-muted mb-1">Period</p>
                        <p className="text-sm font-semibold text-text-primary">{selectedRange}</p>
                    </div>
                </div>
            </div>

            {/* Chart */}
            <div className="px-2 pb-4">
                <TradingChart
                    data={filteredData}
                    height={300}
                    type="area"
                    timeframe={selectedRange}
                    colors={{
                        line: isPositive ? '#10b981' : '#ef4444',
                        areaTop: isPositive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)',
                        areaBottom: 'transparent',
                    }}
                />
            </div>
        </PremiumCard>
    );
}
