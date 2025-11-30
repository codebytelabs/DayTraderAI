import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Activity, DollarSign, Wallet, Clock } from 'lucide-react';
import { AnimatedCurrency, AnimatedPercent } from '../ui/AnimatedNumber';
import { MetricCardSkeleton } from '../ui/LoadingStates';
import { StatusBadge } from '../ui/StatusBadge';
import type { AccountInfo, MarketStatus } from '../../hooks/useMarketData';

interface MarketOverviewProps {
    account: AccountInfo | null;
    marketStatus: MarketStatus | null;
}

export function MarketOverview({ account, marketStatus }: MarketOverviewProps) {
    if (!account) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
                {[1, 2, 3, 4].map((i) => (
                    <MetricCardSkeleton key={i} />
                ))}
            </div>
        );
    }

    const dailyPL = account.equity - account.last_equity;
    const dailyPLPct = account.last_equity ? (dailyPL / account.last_equity) * 100 : 0;
    const isProfit = dailyPL >= 0;

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    };

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
    };

    return (
        <motion.div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-6"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
        >
            {/* Total Equity */}
            <motion.div
                className="glass-panel p-5 relative overflow-hidden group"
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                transition={{ duration: 0.2 }}
            >
                <div className="flex items-start justify-between relative z-10">
                    <div>
                        <p className="text-sm font-medium text-text-secondary mb-2">Total Equity</p>
                        <div className="text-2xl font-bold text-white metric-value">
                            <AnimatedCurrency value={account.equity} />
                        </div>
                        <p className="text-xs text-text-muted mt-2">
                            Cash: ${account.cash.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                        </p>
                    </div>
                    <div className="p-3 rounded-xl bg-primary/10 text-primary group-hover:bg-primary/20 transition-colors">
                        <DollarSign className="w-5 h-5" />
                    </div>
                </div>
                <div className="absolute -right-8 -bottom-8 w-32 h-32 rounded-full bg-primary/5 blur-2xl group-hover:bg-primary/10 transition-colors" />
            </motion.div>

            {/* Daily P&L */}
            <motion.div
                className="glass-panel p-5 relative overflow-hidden group"
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                transition={{ duration: 0.2 }}
            >
                <div className="flex items-start justify-between relative z-10">
                    <div>
                        <p className="text-sm font-medium text-text-secondary mb-2">Daily P&L</p>
                        <div className={`text-2xl font-bold metric-value ${isProfit ? 'text-success glow-success' : 'text-danger glow-danger'}`}>
                            <AnimatedCurrency value={dailyPL} showSign />
                        </div>
                        <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${isProfit ? 'text-success' : 'text-danger'}`}>
                            {isProfit ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                            <AnimatedPercent value={dailyPLPct} />
                        </div>
                    </div>
                    <div className={`p-3 rounded-xl ${isProfit ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'} group-hover:scale-110 transition-transform`}>
                        {isProfit ? <TrendingUp className="w-5 h-5" /> : <TrendingDown className="w-5 h-5" />}
                    </div>
                </div>
                <div className={`absolute -right-8 -bottom-8 w-32 h-32 rounded-full ${isProfit ? 'bg-success/5' : 'bg-danger/5'} blur-2xl`} />
            </motion.div>

            {/* Buying Power */}
            <motion.div
                className="glass-panel p-5 relative overflow-hidden group"
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                transition={{ duration: 0.2 }}
            >
                <div className="flex items-start justify-between relative z-10">
                    <div>
                        <p className="text-sm font-medium text-text-secondary mb-2">Buying Power</p>
                        <div className="text-2xl font-bold text-white metric-value">
                            <AnimatedCurrency value={account.buying_power} />
                        </div>
                        <p className="text-xs text-text-muted mt-2">
                            Cash: <AnimatedCurrency value={account.cash} />
                        </p>
                    </div>
                    <div className="p-3 rounded-xl bg-accent/10 text-accent group-hover:bg-accent/20 transition-colors">
                        <Wallet className="w-5 h-5" />
                    </div>
                </div>
                <div className="absolute -right-8 -bottom-8 w-32 h-32 rounded-full bg-accent/5 blur-2xl" />
            </motion.div>

            {/* Market Status */}
            <motion.div
                className="glass-panel p-5 relative overflow-hidden group"
                variants={itemVariants}
                whileHover={{ scale: 1.02, y: -2 }}
                transition={{ duration: 0.2 }}
            >
                <div className="flex items-start justify-between relative z-10">
                    <div>
                        <p className="text-sm font-medium text-text-secondary mb-2">Market Status</p>
                        <div className="flex items-center gap-2 mb-2">
                            <StatusBadge
                                variant={marketStatus?.isOpen ? 'success' : 'danger'}
                                pulse={marketStatus?.isOpen}
                            >
                                {marketStatus?.isOpen ? 'OPEN' : 'CLOSED'}
                            </StatusBadge>
                        </div>
                        <p className="text-xs text-text-muted mt-2 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {marketStatus?.isOpen
                                ? `Closes in ${Math.max(0, Math.floor((new Date(marketStatus.nextClose!).getTime() - Date.now()) / 3600000))}h`
                                : marketStatus?.nextOpen
                                    ? `Opens in ${Math.max(0, Math.floor((new Date(marketStatus.nextOpen).getTime() - Date.now()) / 3600000))}h`
                                    : 'Weekend'
                            }
                        </p>
                    </div>
                    <div className={`p-3 rounded-xl ${marketStatus?.isOpen ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                        <Activity className="w-5 h-5" />
                    </div>
                </div>
                <div className={`absolute -right-8 -bottom-8 w-32 h-32 rounded-full ${marketStatus?.isOpen ? 'bg-success/5' : 'bg-danger/5'} blur-2xl`} />
            </motion.div>
        </motion.div>
    );
}
