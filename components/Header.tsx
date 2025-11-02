
import React, { useMemo } from 'react';
import { ConnectionStatuses, ServiceStatus } from '../types';
import { useServiceHealth } from '../hooks/useServiceHealth';
import { useTrading } from '../state/TradingContext';

const StatusIndicator: React.FC<{ status: ServiceStatus; name: string }> = ({ status, name }) => {
  const statusConfig = {
    [ServiceStatus.CONNECTED]: { color: 'bg-green-500', text: 'Connected' },
    [ServiceStatus.DEGRADED]: { color: 'bg-yellow-500', text: 'Degraded' },
    [ServiceStatus.DISCONNECTED]: { color: 'bg-red-500', text: 'Disconnected' },
  };

  return (
    <div className="flex items-center space-x-2">
      <div className={`w-3 h-3 rounded-full ${statusConfig[status].color}`}></div>
      <span className="text-sm text-brand-text-secondary hidden sm:inline">{name}: <span className="text-brand-text">{statusConfig[status].text}</span></span>
    </div>
  );
};

interface HeaderProps {
  onOpenSettings: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onOpenSettings }) => {
  const health = useServiceHealth();
  const { streamingStatus } = useTrading();

  // Map health status to ServiceStatus enum
  const statuses: ConnectionStatuses = useMemo(() => ({
    alpaca: health.alpaca === 'connected' ? ServiceStatus.CONNECTED : ServiceStatus.DISCONNECTED,
    supabase: health.supabase === 'connected' ? ServiceStatus.CONNECTED : ServiceStatus.DISCONNECTED,
    perplexity: health.perplexity === 'connected' ? ServiceStatus.CONNECTED : ServiceStatus.DISCONNECTED,
    openRouter: health.openrouter === 'connected' ? ServiceStatus.CONNECTED : ServiceStatus.DISCONNECTED,
  }), [health]);

  const streamingServiceStatus: ServiceStatus = useMemo(() => {
    if (streamingStatus === 'connected') return ServiceStatus.CONNECTED;
    if (streamingStatus === 'connecting') return ServiceStatus.DEGRADED;
    if (streamingStatus === 'disabled') return ServiceStatus.DEGRADED;
    return ServiceStatus.DISCONNECTED;
  }, [streamingStatus]);

  return (
    <header className="bg-brand-surface p-4 flex justify-between items-center border-b border-brand-surface-2">
      <h1 className="text-xl sm:text-2xl font-bold text-brand-text">
        Expert Day-Trading Bot
      </h1>
      <div className="flex items-center space-x-4">
        <StatusIndicator status={statuses.alpaca} name="Alpaca" />
        <StatusIndicator status={statuses.supabase} name="Supabase" />
        <StatusIndicator status={statuses.perplexity} name="Perplexity" />
        <StatusIndicator status={statuses.openRouter} name="OpenRouter" />
        <StatusIndicator status={streamingServiceStatus} name="Streaming" />
        <button
          type="button"
          onClick={onOpenSettings}
          className="px-3 py-2 bg-brand-accent hover:bg-brand-accent-hover text-sm font-semibold rounded-md transition"
        >
          Settings
        </button>
      </div>
    </header>
  );
};
