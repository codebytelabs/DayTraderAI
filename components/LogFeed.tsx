
import React, { useRef, useEffect } from 'react';
import { LogEntry, LogLevel } from '../types';

interface LogFeedProps {
  logs: LogEntry[];
}

export const LogFeed: React.FC<LogFeedProps> = ({ logs }) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  console.log('[LogFeed] Received logs:', logs.length);

  const getLogLevelColor = (level: LogLevel) => {
    switch (level) {
      case LogLevel.INFO:
        return 'text-sky-400';
      case LogLevel.WARN:
        return 'text-brand-warning';
      case LogLevel.ERROR:
        return 'text-brand-danger';
      default:
        return 'text-brand-text-secondary';
    }
  };
  
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [logs]);


  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Live Logs</h3>
      <div ref={logContainerRef} className="font-mono text-xs text-brand-text-secondary space-y-1 h-72 overflow-y-auto pr-2 flex flex-col-reverse">
        {/* We reverse here to make new logs appear at the top with flex-col-reverse */}
        <div>
        {logs.slice().reverse().map((log) => (
          <div key={log.id} className="flex">
            <span className="flex-shrink-0 mr-2">{new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
            <span className={`font-bold mr-2 w-12 text-center ${getLogLevelColor(log.level)}`}>[{log.level.toUpperCase()}]</span>
            <span className="flex-grow break-words">{log.message}</span>
          </div>
        ))}
        </div>
      </div>
    </div>
  );
};
