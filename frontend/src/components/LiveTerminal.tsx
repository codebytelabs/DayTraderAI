import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import '@xterm/xterm/css/xterm.css';
import { useWebSocket } from '../hooks/useWebSocket';
import { PremiumCard } from './ui/PremiumCard';
import { StatusBadge } from './ui/StatusBadge';
import { Terminal as TerminalIcon, Maximize2, Download, Trash2 } from 'lucide-react';

interface LogMessage {
    timestamp: number;
    level: string;
    message: string;
    source: string;
}

export function LiveTerminal() {
    const terminalRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);

    const { isConnected } = useWebSocket({
        url: 'ws://localhost:8006/ws/stream',
        onMessage: (data) => {
            if (data.type === 'log') {
                writeLog(data.payload);
            } else if (data.type === 'snapshot') {
                if (data.payload.logs) {
                    data.payload.logs.forEach((log: LogMessage) => {
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
                background: 'transparent',
                foreground: '#e2e8f0',
                cursor: '#3b82f6',
                cursorAccent: '#0a0e1a',
                selectionBackground: 'rgba(59, 130, 246, 0.3)',
                black: '#1e293b',
                red: '#ef4444',
                green: '#10b981',
                yellow: '#f59e0b',
                blue: '#3b82f6',
                magenta: '#8b5cf6',
                cyan: '#06b6d4',
                white: '#f8fafc',
                brightBlack: '#475569',
                brightRed: '#f87171',
                brightGreen: '#34d399',
                brightYellow: '#fbbf24',
                brightBlue: '#60a5fa',
                brightMagenta: '#a78bfa',
                brightCyan: '#22d3ee',
                brightWhite: '#ffffff',
            },
            fontFamily: '"JetBrains Mono", "SF Mono", "Fira Code", monospace',
            fontSize: 13,
            lineHeight: 1.6,
            cursorBlink: true,
            cursorStyle: 'bar',
            convertEol: true,
            allowTransparency: true,
            scrollback: 1000,
        });

        const fitAddon = new FitAddon();
        term.loadAddon(fitAddon);

        term.open(terminalRef.current);
        fitAddon.fit();

        xtermRef.current = term;
        fitAddonRef.current = fitAddon;

        // Welcome message
        term.writeln('');
        term.writeln('\x1b[1;38;5;39m  ╔══════════════════════════════════════════════════════════╗\x1b[0m');
        term.writeln('\x1b[1;38;5;39m  ║\x1b[0m  \x1b[1;37mDayTraderAI\x1b[0m \x1b[38;5;39mLive Terminal\x1b[0m                               \x1b[1;38;5;39m║\x1b[0m');
        term.writeln('\x1b[1;38;5;39m  ╚══════════════════════════════════════════════════════════╝\x1b[0m');
        term.writeln('');
        term.writeln('\x1b[38;5;245m  Initializing connection to trading engine...\x1b[0m');
        term.writeln('');

        const handleResize = () => {
            fitAddon.fit();
        };

        window.addEventListener('resize', handleResize);
        setTimeout(() => fitAddon.fit(), 100);

        return () => {
            window.removeEventListener('resize', handleResize);
            term.dispose();
        };
    }, []);

    useEffect(() => {
        if (xtermRef.current) {
            if (isConnected) {
                xtermRef.current.writeln('\x1b[1;32m  ✓ Connected to backend stream\x1b[0m');
                xtermRef.current.writeln('');
            } else {
                xtermRef.current.writeln('\x1b[1;31m  ✗ Disconnected. Attempting to reconnect...\x1b[0m');
            }
        }
    }, [isConnected]);

    const writeLog = (log: LogMessage) => {
        if (!xtermRef.current) return;

        const timestamp = typeof log.timestamp === 'number'
            ? new Date(log.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
            : new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

        const levelColors: Record<string, string> = {
            'DEBUG': '\x1b[38;5;245m',
            'INFO': '\x1b[38;5;39m',
            'WARNING': '\x1b[38;5;214m',
            'ERROR': '\x1b[38;5;196m',
            'CRITICAL': '\x1b[1;38;5;196m',
        };

        const color = levelColors[log.level] || '\x1b[37m';
        const levelPadded = log.level.padEnd(8);
        const sourcePadded = log.source.slice(0, 12).padEnd(12);

        const line = `\x1b[38;5;245m${timestamp}\x1b[0m ${color}${levelPadded}\x1b[0m \x1b[38;5;141m${sourcePadded}\x1b[0m ${log.message}`;
        xtermRef.current.writeln(line);
    };

    const clearTerminal = () => {
        if (xtermRef.current) {
            xtermRef.current.clear();
        }
    };

    return (
        <PremiumCard
            title="Live Terminal"
            icon={<TerminalIcon className="w-5 h-5" />}
            className="h-full min-h-[500px] flex flex-col"
            action={
                <div className="flex items-center gap-2">
                    <StatusBadge
                        variant={isConnected ? 'success' : 'danger'}
                        pulse={isConnected}
                        size="sm"
                    >
                        {isConnected ? 'CONNECTED' : 'OFFLINE'}
                    </StatusBadge>
                    <div className="flex items-center gap-1 ml-2">
                        <motion.button
                            onClick={clearTerminal}
                            className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-surface transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            title="Clear terminal"
                        >
                            <Trash2 className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                            className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-surface transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            title="Download logs"
                        >
                            <Download className="w-4 h-4" />
                        </motion.button>
                        <motion.button
                            className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-surface transition-colors"
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            title="Fullscreen"
                        >
                            <Maximize2 className="w-4 h-4" />
                        </motion.button>
                    </div>
                </div>
            }
        >
            <div className="flex-1 rounded-xl overflow-hidden bg-[#0a0e1a] border border-glass-border/50">
                <div ref={terminalRef} className="h-full w-full p-2" />
            </div>
        </PremiumCard>
    );
}
