import { motion } from 'framer-motion';
import { Shield, Wifi, Server, Cpu, Activity, CheckCircle2, AlertCircle } from 'lucide-react';
import { PremiumCard } from '../ui/PremiumCard';
import { PulsingDot } from '../ui/LoadingStates';
import type { MarketStatus } from '../../hooks/useMarketData';

interface SystemStatusProps {
    marketStatus: MarketStatus | null;
    error: string | null;
}

interface StatusItemProps {
    icon: React.ReactNode;
    label: string;
    status: 'online' | 'offline' | 'warning' | 'initializing';
    detail?: string;
}

function StatusItem({ icon, label, status, detail }: StatusItemProps) {
    const statusConfig = {
        online: { color: 'text-success', bg: 'bg-success/10', label: 'Online', dot: 'success' as const },
        offline: { color: 'text-danger', bg: 'bg-danger/10', label: 'Offline', dot: 'danger' as const },
        warning: { color: 'text-warning', bg: 'bg-warning/10', label: 'Warning', dot: 'warning' as const },
        initializing: { color: 'text-primary', bg: 'bg-primary/10', label: 'Initializing', dot: 'primary' as const },
    };

    const config = statusConfig[status];

    return (
        <motion.div
            className="flex items-center justify-between py-3 border-b border-glass-border/30 last:border-0"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
        >
            <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${config.bg} ${config.color}`}>
                    {icon}
                </div>
                <div>
                    <p className="text-sm font-medium text-text-primary">{label}</p>
                    {detail && <p className="text-xs text-text-muted">{detail}</p>}
                </div>
            </div>
            <div className="flex items-center gap-2">
                <PulsingDot color={config.dot} />
                <span className={`text-xs font-semibold ${config.color}`}>
                    {config.label}
                </span>
            </div>
        </motion.div>
    );
}

export function SystemStatus({ marketStatus, error }: SystemStatusProps) {
    const isConnected = !error;
    const isEngineActive = !!marketStatus;

    return (
        <PremiumCard
            title="System Status"
            icon={<Activity className="w-5 h-5" />}
        >
            <div className="space-y-1">
                <StatusItem
                    icon={<Wifi className="w-4 h-4" />}
                    label="WebSocket Connection"
                    status={isConnected ? 'online' : 'offline'}
                    detail={isConnected ? 'Real-time data streaming' : 'Reconnecting...'}
                />
                <StatusItem
                    icon={<Server className="w-4 h-4" />}
                    label="Trading Engine"
                    status={isEngineActive ? 'online' : 'initializing'}
                    detail={isEngineActive ? 'Processing signals' : 'Starting up...'}
                />
                <StatusItem
                    icon={<Shield className="w-4 h-4" />}
                    label="Risk Guard"
                    status="online"
                    detail="Position limits active"
                />
                <StatusItem
                    icon={<Cpu className="w-4 h-4" />}
                    label="AI Scanner"
                    status="online"
                    detail="Scanning opportunities"
                />
            </div>

            {/* Overall Status */}
            <motion.div
                className={`mt-4 p-4 rounded-xl ${isConnected && isEngineActive ? 'bg-success/10 border border-success/20' : 'bg-warning/10 border border-warning/20'}`}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
            >
                <div className="flex items-center gap-3">
                    {isConnected && isEngineActive ? (
                        <>
                            <CheckCircle2 className="w-5 h-5 text-success" />
                            <div>
                                <p className="text-sm font-semibold text-success">All Systems Operational</p>
                                <p className="text-xs text-text-muted">Bot is actively trading</p>
                            </div>
                        </>
                    ) : (
                        <>
                            <AlertCircle className="w-5 h-5 text-warning" />
                            <div>
                                <p className="text-sm font-semibold text-warning">System Initializing</p>
                                <p className="text-xs text-text-muted">Please wait...</p>
                            </div>
                        </>
                    )}
                </div>
            </motion.div>
        </PremiumCard>
    );
}
