
import React, { useState, useEffect } from 'react';
import { ConnectionStatuses, ServiceStatus } from '../types';

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

export const Header: React.FC = () => {
    const [statuses, setStatuses] = useState<ConnectionStatuses>({
        alpaca: ServiceStatus.CONNECTED,
        supabase: ServiceStatus.CONNECTED,
        perplexity: ServiceStatus.DEGRADED,
        openRouter: ServiceStatus.CONNECTED,
    });

    // Mock status changes
    useEffect(() => {
        const interval = setInterval(() => {
            setStatuses(prev => ({
                ...prev,
                perplexity: Math.random() > 0.8 ? ServiceStatus.DISCONNECTED : ServiceStatus.CONNECTED,
                supabase: Math.random() > 0.95 ? ServiceStatus.DEGRADED : ServiceStatus.CONNECTED,
            }))
        }, 15000);
        return () => clearInterval(interval);
    }, []);

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
      </div>
    </header>
  );
};
