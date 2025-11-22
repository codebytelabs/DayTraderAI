import { useState, useEffect, useCallback } from 'react';

const API_BASE_URL = 'http://localhost:8000';

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

            if (positionsRes.ok) setPositions(await positionsRes.json());
            if (accountRes.ok) setAccount(await accountRes.json());
            if (marketStatusRes.ok) setMarketStatus(await marketStatusRes.json());
            if (opportunitiesRes.ok) setOpportunities(await opportunitiesRes.json());
            if (historyRes.ok) setPortfolioHistory(await historyRes.json());

            setError(null);
        } catch (err) {
            console.error('Failed to fetch market data:', err);
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
