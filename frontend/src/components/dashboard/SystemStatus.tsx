import React from 'react';
import { GlassCard } from '../layout/GlassCard';
import { Shield, Wifi, Server } from 'lucide-react';
import type { MarketStatus } from '../../hooks/useMarketData';

interface SystemStatusProps {
    marketStatus: MarketStatus | null;
    error: string | null;
}

export function SystemStatus({ marketStatus, error }: SystemStatusProps) {
    return (
        <GlassCard className="p-6">
            <h2 className="text-lg font-semibold text-glass-text-primary mb-4">System Status</h2>
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center text-glass-text-secondary">
                        <Wifi className="w-4 h-4 mr-2" />
                        <span className="text-sm">Connection</span>
                    </div>
                    <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${error ? 'bg-danger' : 'bg-success'}`}></div>
                        <span className={`text-sm font-medium ${error ? 'text-danger' : 'text-success'}`}>
                            {error ? 'Disconnected' : 'Connected'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <div className="flex items-center text-glass-text-secondary">
                        <Server className="w-4 h-4 mr-2" />
                        <span className="text-sm">Trading Engine</span>
                    </div>
                    <div className="flex items-center">
                        <div className={`w-2 h-2 rounded-full mr-2 ${marketStatus ? 'bg-success' : 'bg-warning'}`}></div>
                        <span className={`text-sm font-medium ${marketStatus ? 'text-success' : 'text-warning'}`}>
                            {marketStatus ? 'Active' : 'Initializing'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center justify-between">
                    <div className="flex items-center text-glass-text-secondary">
                        <Shield className="w-4 h-4 mr-2" />
                        <span className="text-sm">Risk Guard</span>
                    </div>
                    <div className="flex items-center">
                        <div className="w-2 h-2 rounded-full bg-success mr-2"></div>
                        <span className="text-sm font-medium text-success">Active</span>
                    </div>
                </div>
            </div>
        </GlassCard>
    );
}
