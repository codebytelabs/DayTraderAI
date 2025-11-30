import { motion, AnimatePresence } from 'framer-motion';
import { Zap, ArrowRight, Clock, TrendingUp, Sparkles, Target } from 'lucide-react';
import { PremiumCard } from '../ui/PremiumCard';
import { LiveIndicator } from '../ui/StatusBadge';
import type { Opportunity } from '../../hooks/useMarketData';

interface OpportunityFeedProps {
    opportunities: Opportunity[];
}

function getScoreColor(score: number) {
    if (score >= 80) return 'text-success bg-success/10 border-success/30';
    if (score >= 60) return 'text-primary bg-primary/10 border-primary/30';
    if (score >= 40) return 'text-warning bg-warning/10 border-warning/30';
    return 'text-text-secondary bg-surface border-glass-border';
}

function getTypeIcon(type: string) {
    switch (type.toLowerCase()) {
        case 'momentum':
            return <TrendingUp className="w-4 h-4" />;
        case 'breakout':
            return <Zap className="w-4 h-4" />;
        case 'reversal':
            return <Target className="w-4 h-4" />;
        default:
            return <Sparkles className="w-4 h-4" />;
    }
}

export function OpportunityFeed({ opportunities }: OpportunityFeedProps) {
    return (
        <PremiumCard
            title="AI Opportunities"
            icon={<Zap className="w-5 h-5" />}
            action={<LiveIndicator />}
            className="h-full"
        >
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 -mr-2">
                <AnimatePresence mode="popLayout">
                    {opportunities.length === 0 ? (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="flex flex-col items-center justify-center py-12 text-center"
                        >
                            <div className="w-16 h-16 rounded-2xl bg-surface flex items-center justify-center mb-4">
                                <Sparkles className="w-8 h-8 text-text-muted" />
                            </div>
                            <p className="text-text-secondary font-medium mb-1">No opportunities found</p>
                            <p className="text-text-muted text-sm">AI is scanning the market...</p>
                        </motion.div>
                    ) : (
                        opportunities.map((opp, index) => (
                            <motion.div
                                key={`${opp.symbol}-${opp.timestamp}`}
                                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                                transition={{ delay: index * 0.05 }}
                                className="group relative p-4 rounded-xl bg-surface/50 border border-glass-border hover:border-primary/30 hover:bg-surface/80 transition-all cursor-pointer"
                                whileHover={{ scale: 1.01, y: -2 }}
                            >
                                {/* Glow effect on hover */}
                                <div className="absolute inset-0 rounded-xl bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                
                                <div className="relative">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex items-center gap-3">
                                            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 flex items-center justify-center">
                                                <span className="text-sm font-bold text-white">{opp.symbol.slice(0, 4)}</span>
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="font-semibold text-white">{opp.symbol}</span>
                                                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold border ${getScoreColor(opp.score)}`}>
                                                        {getTypeIcon(opp.type)}
                                                        {opp.score.toFixed(0)}%
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <span className="text-xs text-text-muted capitalize">{opp.type}</span>
                                                    <span className="text-text-muted">•</span>
                                                    <span className="text-xs text-text-muted flex items-center gap-1">
                                                        <Clock className="w-3 h-3" />
                                                        {new Date(opp.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-bold text-white">${opp.price.toFixed(2)}</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between pt-3 border-t border-glass-border/30">
                                        <span className="text-xs text-text-muted font-medium px-2 py-1 bg-surface rounded-md">
                                            {opp.source}
                                        </span>
                                        <motion.button
                                            className="flex items-center gap-1 text-xs font-semibold text-primary opacity-0 group-hover:opacity-100 transition-opacity"
                                            whileHover={{ x: 3 }}
                                        >
                                            Analyze <ArrowRight className="w-3 h-3" />
                                        </motion.button>
                                    </div>
                                </div>
                            </motion.div>
                        ))
                    )}
                </AnimatePresence>
            </div>

            {opportunities.length > 0 && (
                <motion.div
                    className="mt-4 pt-4 border-t border-glass-border"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                >
                    <button className="w-full btn-secondary text-sm flex items-center justify-center gap-2">
                        <Sparkles className="w-4 h-4" />
                        View All Opportunities
                    </button>
                </motion.div>
            )}
        </PremiumCard>
    );
}
