
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
        return 'text-yellow-400';
      case LogLevel.ERROR:
        return 'text-rose-400';
      default:
        return 'text-slate-400';
    }
  };
  
  const getLogLevelBg = (level: LogLevel) => {
    switch (level) {
      case LogLevel.INFO:
        return 'bg-sky-500/10';
      case LogLevel.WARN:
        return 'bg-yellow-500/10';
      case LogLevel.ERROR:
        return 'bg-rose-500/10';
      default:
        return 'bg-slate-500/10';
    }
  };
  
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [logs]);

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">📋</span>
        <h3 className="text-xl font-bold text-white">Live Logs</h3>
      </div>
      <div 
        ref={logContainerRef} 
        className="font-mono text-xs space-y-1.5 h-80 overflow-y-auto pr-2 flex flex-col-reverse scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent"
      >
        <div className="space-y-1.5">
          {logs.slice().reverse().map((log) => (
            <div key={log.id} className="flex items-start gap-2 p-2 rounded-md hover:bg-slate-800/30 transition-colors">
              <span className="flex-shrink-0 text-slate-500 font-medium">
                {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </span>
              <span className={`flex-shrink-0 px-2 py-0.5 rounded text-xs font-bold ${getLogLevelColor(log.level)} ${getLogLevelBg(log.level)}`}>
                {log.level.toUpperCase()}
              </span>
              <span className="flex-grow text-slate-300 break-words">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
