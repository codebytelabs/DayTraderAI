import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketOptions {
    url: string;
    onMessage?: (data: any) => void;
    onOpen?: () => void;
    onClose?: () => void;
    onError?: (error: Event) => void;
    reconnectInterval?: number;
}

export function useWebSocket({
    url,
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnectInterval = 3000,
}: WebSocketOptions) {
    const ws = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

    const connect = useCallback(() => {
        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                setIsConnected(true);
                onOpen?.();
            };

            ws.current.onclose = () => {
                setIsConnected(false);
                onClose?.();
                // Attempt reconnect
                reconnectTimeout.current = setTimeout(connect, reconnectInterval);
            };

            ws.current.onerror = (error) => {
                onError?.(error);
                ws.current?.close();
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage?.(data);
                } catch (e) {
                    console.error('Failed to parse WebSocket message:', e);
                }
            };
        } catch (e) {
            console.error('WebSocket connection failed:', e);
            reconnectTimeout.current = setTimeout(connect, reconnectInterval);
        }
    }, [url, onMessage, onOpen, onClose, onError, reconnectInterval]);

    useEffect(() => {
        connect();

        return () => {
            if (ws.current) {
                ws.current.close();
            }
            if (reconnectTimeout.current) {
                clearTimeout(reconnectTimeout.current);
            }
        };
    }, [connect]);

    const sendMessage = useCallback((data: any) => {
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket is not connected');
        }
    }, []);

    return { isConnected, sendMessage };
}
