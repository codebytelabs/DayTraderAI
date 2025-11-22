import React, { useEffect, useRef } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { useWebSocket } from '../hooks/useWebSocket';
import { GlassCard } from './layout/GlassCard';

interface LogMessage {
    timestamp: number;
    level: string;
    message: string;
    source: string;
}

export const LiveTerminal: React.FC = () => {
    const terminalRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);

    const { isConnected } = useWebSocket({
        url: 'ws://localhost:8000/ws/stream',
        onMessage: (data) => {
            if (data.type === 'log') {
                writeLog(data.payload);
            } else if (data.type === 'snapshot') {
                if (data.payload.logs) {
                    data.payload.logs.forEach((log: any) => {
                        writeLog(log);
                    });
                }
            }
        },
    });

    useEffect(() => {
        if (!terminalRef.current) return;

        const term = new Terminal({
            theme: {
                background: '#00000000', // Transparent to let glass background show
                foreground: '#e2e8f0',
                cursor: '#3b82f6',
                selectionBackground: 'rgba(59, 130, 246, 0.3)',
            },
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 12,
            lineHeight: 1.5,
            cursorBlink: true,
            convertEol: true,
            allowTransparency: true,
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);

        term.open(terminalRef.current);
        fitAddon.fit();

        xtermRef.current = term;
        fitAddonRef.current = fitAddon;

        term.writeln('\x1b[1;34m> DayTraderAI System Initialized\x1b[0m');
        term.writeln('> Waiting for connection...');

        const handleResize = () => fitAddon.fit();
        window.addEventListener('resize', handleResize);

        // Initial fit after a short delay to ensure container is rendered
        setTimeout(() => fitAddon.fit(), 100);

        return () => {
            window.removeEventListener('resize', handleResize);
            term.dispose();
        };
    }, []);

    useEffect(() => {
        if (xtermRef.current) {
            if (isConnected) {
                xtermRef.current.writeln('\x1b[1;32m> Connected to backend stream\x1b[0m');
            } else {
                xtermRef.current.writeln('\x1b[1;31m> Disconnected. Reconnecting...\x1b[0m');
            }
        }
    }, [isConnected]);

    const writeLog = (log: LogMessage | any) => {
        if (!xtermRef.current) return;

        const timestamp = typeof log.timestamp === 'number'
            ? new Date(log.timestamp * 1000).toLocaleTimeString()
            : new Date(log.timestamp).toLocaleTimeString();

        let color = '\x1b[37m'; // White
        if (log.level === 'INFO') color = '\x1b[36m'; // Cyan
        if (log.level === 'WARNING') color = '\x1b[33m'; // Yellow
        if (log.level === 'ERROR') color = '\x1b[31m'; // Red
        if (log.level === 'CRITICAL') color = '\x1b[1;31m'; // Bold Red

        const line = `\x1b[90m[${timestamp}]\x1b[0m ${color}[${log.level}]\x1b[0m \x1b[35m[${log.source}]\x1b[0m ${log.message}`;
        xtermRef.current.writeln(line);
    };

    return (
        <GlassCard title="Live Terminal" className="h-full min-h-[500px]">
            <div className="flex items-center justify-between mb-2 px-2">
                <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-success animate-pulse' : 'bg-danger'}`} />
                    <span className="text-xs text-text-secondary font-mono">
                        {isConnected ? 'ONLINE' : 'OFFLINE'}
                    </span>
                </div>
            </div>
            <div className="flex-1 rounded-lg overflow-hidden bg-black/20 p-2 h-[calc(100%-2rem)]">
                <div ref={terminalRef} className="h-full w-full" />
            </div>
        </GlassCard>
    );
};

