import React from 'react';
import { StreamingStatus } from '../hooks/useBackendTrading';

interface WebSocketStatusProps {
  status: StreamingStatus;
  className?: string;
}

export const WebSocketStatus: React.FC<WebSocketStatusProps> = ({ status, className = '' }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          color: 'bg-green-500',
          text: 'Live',
          pulse: 'animate-pulse',
        };
      case 'connecting':
        return {
          color: 'bg-yellow-500',
          text: 'Connecting',
          pulse: 'animate-pulse',
        };
      case 'error':
        return {
          color: 'bg-red-500',
          text: 'Disconnected',
          pulse: '',
        };
      case 'disabled':
        return {
          color: 'bg-gray-500',
          text: 'Disabled',
          pulse: '',
        };
      default:
        return {
          color: 'bg-gray-500',
          text: 'Unknown',
          pulse: '',
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="relative flex items-center">
        <div className={`h-2 w-2 rounded-full ${config.color} ${config.pulse}`} />
        {status === 'connected' && (
          <div className="absolute h-2 w-2 rounded-full bg-green-500 animate-ping opacity-75" />
        )}
      </div>
      <span className="text-xs font-medium text-gray-700 dark:text-gray-300">
        {config.text}
      </span>
    </div>
  );
};
