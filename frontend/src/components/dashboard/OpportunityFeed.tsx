import React from 'react';
import { GlassCard } from '../layout/GlassCard';
import { Zap, ArrowRight, Clock } from 'lucide-react';
import type { Opportunity } from '../../hooks/useMarketData';

interface OpportunityFeedProps {
    opportunities: Opportunity[];
}

export function OpportunityFeed({ opportunities }: OpportunityFeedProps) {
    return (
        <GlassCard className="p-6 h-full">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                    <div className="p-2 bg-accent/10 rounded-lg text-accent">
                        <Zap className="w-5 h-5" />
                    </div>
                    <h2 className="text-lg font-semibold text-glass-text-primary">AI Opportunities</h2>
                </div>
                <span className="text-xs font-medium px-2 py-1 bg-glass-surface rounded-full text-glass-text-secondary">
                    Live Feed
                </span>
            </div>

            <div className="space-y-4">
                {opportunities.length === 0 ? (
                    <div className="text-center py-8 text-glass-text-secondary">
                        No opportunities found
                    </div>
                ) : (
                    opportunities.map((opp, index) => (
                        <div key={index} className="p-4 rounded-xl bg-glass-surface/30 border border-glass-border hover:bg-glass-surface/50 transition-all cursor-pointer group">
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex items-center space-x-3">
                                    <div className="w-10 h-10 rounded-lg bg-glass-surface flex items-center justify-center font-bold text-glass-text-primary">
                                        {opp.symbol}
                                    </div>
                                    <div>
                                        <div className="flex items-center space-x-2">
                                            <span className="font-semibold text-glass-text-primary">{opp.type}</span>
                                            <span className="text-xs px-1.5 py-0.5 rounded bg-success/10 text-success font-medium">
                                                {opp.score.toFixed(0)}% Match
                                            </span>
                                        </div>
                                        <div className="flex items-center text-xs text-glass-text-secondary mt-0.5">
                                            <Clock className="w-3 h-3 mr-1" />
                                            {new Date(opp.timestamp).toLocaleTimeString()}
                                        </div>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-medium text-glass-text-primary">
                                        ${opp.price.toFixed(2)}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between mt-3 pt-3 border-t border-glass-border/50">
                                <span className="text-xs text-glass-text-secondary font-medium">
                                    {opp.source}
                                </span>
                                <button className="text-xs font-medium text-accent flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                                    Analyze <ArrowRight className="w-3 h-3 ml-1" />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </GlassCard>
    );
}
