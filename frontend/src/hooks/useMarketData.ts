import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8006';

export interface Position {
    symbol: string;
    qty: number;
    side: 'buy' | 'sell';
    avg_entry_price: number;
    current_price: number;
    unrealized_pl: number;
    unrealized_pl_pct: number;
    market_value: number;
}

export interface AccountInfo {
    equity: number;
    cash: number;
    buying_power: number;
    portfolio_value: number;
    last_equity: number;
    currency: string;
}

export interface MarketStatus {
    isOpen: boolean;
    nextOpen: string | null;
    nextClose: string | null;
    currentTime: string;
}

export interface Opportunity {
    symbol: string;
    score: number;
    price: number;
    type: string;
    source: string;
    timestamp: string;
}

export interface PortfolioHistoryPoint {
    timestamp: number;
    equity: number;
    pnl: number;
    pnl_pct: number;
}

export function useMarketData() {
    const [positions, setPositions] = useState<Position[]>([]);
    const [account, setAccount] = useState<AccountInfo | null>(null);
    const [marketStatus, setMarketStatus] = useState<MarketStatus | null>(null);
    const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
    const [portfolioHistory, setPortfolioHistory] = useState<PortfolioHistoryPoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        try {
            console.log('🔄 Fetching market data from:', API_BASE_URL);
            const [
                positionsRes,
                accountRes,
                marketStatusRes,
                opportunitiesRes,
                historyRes
            ] = await Promise.all([
                fetch(`${API_BASE_URL}/positions`),
                fetch(`${API_BASE_URL}/account`),
                fetch(`${API_BASE_URL}/market/status`),
                fetch(`${API_BASE_URL}/scanner/opportunities?limit=5`),
                fetch(`${API_BASE_URL}/performance?timeframe=1D`)
            ]);

            console.log('📊 Response statuses:', {
                positions: positionsRes.status,
                account: accountRes.status,
                marketStatus: marketStatusRes.status,
                opportunities: opportunitiesRes.status,
                history: historyRes.status
            });

            if (positionsRes.ok) {
                const data = await positionsRes.json();
                console.log('📈 Positions:', data.length, 'items', data);
                setPositions(Array.isArray(data) ? data : []);
            } else {
                console.error('❌ Positions fetch failed:', positionsRes.status);
            }
            if (accountRes.ok) {
                const data = await accountRes.json();
                console.log('💰 Account:', data);
                setAccount(data);
            } else {
                console.error('❌ Account fetch failed:', accountRes.status);
            }
            if (marketStatusRes.ok) {
                const data = await marketStatusRes.json();
                console.log('🏪 Market Status:', data);
                setMarketStatus(data);
            } else {
                console.error('❌ Market status fetch failed:', marketStatusRes.status);
            }
            if (opportunitiesRes.ok) {
                const data = await opportunitiesRes.json();
                console.log('🎯 Opportunities:', data);
                setOpportunities(Array.isArray(data) ? data : []);
            } else {
                console.error('❌ Opportunities fetch failed:', opportunitiesRes.status);
            }
            if (historyRes.ok) {
                const data = await historyRes.json();
                console.log('📉 History:', Array.isArray(data) ? data.length : 'not array', data);
                setPortfolioHistory(Array.isArray(data) ? data : []);
            } else {
                console.error('❌ History fetch failed:', historyRes.status);
            }

            setError(null);
        } catch (err) {
            console.error('❌ Failed to fetch market data:', err);
            setError('Failed to connect to trading engine');
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, [fetchData]);

    return {
        positions,
        account,
        marketStatus,
        opportunities,
        portfolioHistory,
        isLoading,
        error,
        refresh: fetchData
    };
}
