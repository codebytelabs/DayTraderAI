import React from 'react';
import { GlassCard } from '../layout/GlassCard';
import { TrendingUp, TrendingDown, Activity, DollarSign } from 'lucide-react';
import type { AccountInfo, MarketStatus } from '../../hooks/useMarketData';

interface MarketOverviewProps {
    account: AccountInfo | null;
    marketStatus: MarketStatus | null;
}

export const MarketOverview: React.FC<MarketOverviewProps> = ({ account, marketStatus }) => {
    const metrics = [
        {
            label: 'Total Equity',
            value: account ? `$${account.equity.toLocaleString()}` : '---',
            change: account ? `${account.last_equity ? ((account.equity - account.last_equity) / account.last_equity * 100).toFixed(2) : '0.00'}%` : '---',
            isPositive: account ? (account.equity >= account.last_equity) : true,
            icon: DollarSign,
        },
        {
            label: 'Buying Power',
            value: account ? `$${account.buying_power.toLocaleString()}` : '---',
            change: 'Available',
            isPositive: true,
            icon: Activity,
        },
        {
            label: 'Daily P&L',
            value: account ? `$${(account.equity - account.last_equity).toLocaleString()}` : '---',
            change: account ? `${((account.equity - account.last_equity) / account.last_equity * 100).toFixed(2)}%` : '---',
            isPositive: account ? (account.equity >= account.last_equity) : true,
            icon: account && account.equity >= account.last_equity ? TrendingUp : TrendingDown,
        },
        {
            label: 'Market Status',
            value: marketStatus ? (marketStatus.isOpen ? 'OPEN' : 'CLOSED') : '---',
            change: marketStatus ? (marketStatus.isOpen ? `Closes in ${Math.floor((new Date(marketStatus.nextClose!).getTime() - new Date().getTime()) / 3600000)}h` : `Opens in ${Math.floor((new Date(marketStatus.nextOpen!).getTime() - new Date().getTime()) / 3600000)}h`) : '---',
            isPositive: marketStatus?.isOpen ?? false,
            icon: Activity,
        },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            {metrics.map((metric, index) => (
                <GlassCard key={index} className="p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-glass-text-secondary text-sm font-medium mb-1">
                                {metric.label}
                            </p>
                            <h3 className="text-2xl font-bold text-glass-text-primary mb-1">
                                {metric.value}
                            </h3>
                            <div className={`flex items-center text-xs ${metric.isPositive ? 'text-success' : 'text-danger'
                                }`}>
                                {metric.isPositive ? (
                                    <TrendingUp className="w-3 h-3 mr-1" />
                                ) : (
                                    <TrendingDown className="w-3 h-3 mr-1" />
                                )}
                                <span className="font-medium">{metric.change}</span>
                            </div>
                        </div>
                        <div className={`p-3 rounded-xl ${metric.isPositive
                            ? 'bg-success/10 text-success'
                            : 'bg-danger/10 text-danger'
                            }`}>
                            <metric.icon className="w-5 h-5" />
                        </div>
                    </div>
                </GlassCard>
            ))}
        </div>
    );
};
