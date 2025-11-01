import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Position, Order, LogEntry, AdvisoryMessage, PerformanceDataPoint, TradeAnalysis,
  OrderSide, OrderStatus, LogLevel,
} from '../types';

// --- SIMULATION CONFIG ---
const SIMULATED_UNIVERSE = ['SPY', 'QQQ', 'TSLA', 'NVDA', 'AAPL', 'AMD', 'GOOG', 'MSFT', 'AMZN', 'META'];
const INITIAL_EQUITY = 100000;
const TICK_INTERVAL = 500; // Market ticks faster
const CANDLE_INTERVAL = 60 * 1000; // 1-minute candles
const ADVISORY_INTERVAL = 45000; // ms
const MAX_POSITIONS = 5;
const RISK_PER_TRADE = 0.01; // 1% of equity
const STOP_LOSS_ATR_MULT = 2.0;
const TAKE_PROFIT_ATR_MULT = 4.0;
const EMA_SHORT = 9;
const EMA_LONG = 21;

interface TickerData {
  price: number;
  drift: number;
  volatility: number;
  atr: number; 
  emas: { short: number, long: number };
  prevEmas: { short: number, long: number };
}
interface MarketData { [symbol: string]: TickerData; }
interface Stats { dailyPl: number; dailyPlPc: number; winRate: number; profitFactor: number; wins: number; losses: number; }

const generateInitialMarket = (): MarketData => {
  const market: MarketData = {};
  SIMULATED_UNIVERSE.forEach(symbol => {
    const price = 200 + Math.random() * 300;
    market[symbol] = {
      price: price,
      drift: (Math.random() - 0.5) * 0.00001,
      volatility: 0.0001 + Math.random() * 0.0005,
      atr: price * 0.01,
      emas: { short: price, long: price },
      prevEmas: { short: price, long: price },
    };
  });
  return market;
};

export const useTradingSimulator = () => {
  const [market, setMarket] = useState<MarketData>(generateInitialMarket);
  const [positions, setPositions] = useState<Position[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [advisories, setAdvisories] = useState<AdvisoryMessage[]>([]);
  const [tradeAnalyses, setTradeAnalyses] = useState<TradeAnalysis[]>([]);
  const [stats, setStats] = useState<Stats>({ dailyPl: 0, dailyPlPc: 0, winRate: 0, profitFactor: 1, wins: 0, losses: 0 });
  const [performanceData, setPerformanceData] = useState<PerformanceDataPoint[]>([]);

  const idCounter = useRef({ order: 0, position: 0, log: 0, advisory: 0, analysis: 0 });
  const equity = useRef(INITIAL_EQUITY);
  const totalGrossProfit = useRef(0);
  const totalGrossLoss = useRef(0);
  const lastAdvisoryTime = useRef(Date.now());
  const candleTimestamp = useRef(0);
  const currentCandle = useRef<Omit<PerformanceDataPoint, 'timestamp' | 'pnl' | 'winRate' | 'profitFactor' | 'wins' | 'losses'>>({ open: INITIAL_EQUITY, high: INITIAL_EQUITY, low: INITIAL_EQUITY, close: INITIAL_EQUITY });

  const addLog = useCallback((level: LogLevel, message: string) => {
    setLogs(prev => {
        idCounter.current.log++;
        const newLog: LogEntry = { id: idCounter.current.log, timestamp: new Date().toISOString(), level, message };
        return [...prev.slice(-199), newLog];
    });
  }, []);
  
  const generateTradeAnalysis = useCallback((symbol: string, side: OrderSide, entryPrice: number, takeProfit: number, stopLoss: number, reason: string) => {
    addLog(LogLevel.INFO, `Generating simulated AI trade analysis for ${symbol}.`);
    
    // Simulate network delay for a more realistic feel
    setTimeout(() => {
        const direction = side === OrderSide.BUY ? 'LONG' : 'SHORT';
        const rationaleTemplates = [
            `Initiating ${direction} on ${symbol} based on a strong ${reason}. This trade is supported by a confluence of technical signals, including bullish divergence on the 5-min RSI, indicating potential for short-term trend continuation.`,
            `The ${reason} signal for ${symbol} suggests a high-probability entry. Fundamentally, the stock shows strength due to recent positive sector momentum. The position aims to capitalize on the expected short-term trend continuation.`,
            `Executing a ${direction} trade on ${symbol}. The rationale is a clear ${reason} pattern, confirmed by a high-volume engulfing candle pattern. This aligns with our core momentum-based strategy.`
        ];
        
        const reasoning = rationaleTemplates[Math.floor(Math.random() * rationaleTemplates.length)];

        idCounter.current.analysis++;
        const newAnalysis: TradeAnalysis = {
            id: `ta-${idCounter.current.analysis}`,
            timestamp: new Date().toISOString(),
            symbol,
            side,
            entryPrice,
            takeProfit,
            stopLoss,
            reasoning,
            source: 'Gemini' // Keep the source name for UI consistency
        };
        setTradeAnalyses(prev => [newAnalysis, ...prev.slice(0, 49)]);

    }, 800 + Math.random() * 500); // Simulate realistic delay

  }, [addLog]);

  const placeOrder = useCallback((symbol: string, side: OrderSide, qty: number, reason: string) => {
    idCounter.current.order++;
    const newOrder: Order = {
        id: `ord${idCounter.current.order}`, symbol, qty, side, type: 'market',
        status: OrderStatus.OPEN, filledQty: 0, submittedAt: new Date().toISOString(),
    };
    setOrders(prev => [...prev, newOrder]);
    addLog(LogLevel.INFO, `[ORDER PLACED] ${side.toUpperCase()} ${qty} ${symbol}. Reason: ${reason}`);

    setTimeout(() => {
        const fillPrice = market[symbol].price;
        setOrders(prev => prev.map(o => o.id === newOrder.id ? {...o, status: OrderStatus.FILLED, filledQty: qty, filledAvgPrice: fillPrice} : o));
    }, TICK_INTERVAL / 2);
  }, [addLog, market]);
  
  const closePosition = useCallback((positionId: string, reason = "Manual Close") => {
      const pos = positions.find(p => p.id === positionId);
      if (pos) {
          const side = pos.side === OrderSide.BUY ? OrderSide.SELL : OrderSide.BUY;
          placeOrder(pos.symbol, side, pos.qty, reason);
      }
  }, [positions, placeOrder]);

  const cancelOrder = useCallback((orderId: string) => {
    setOrders(prev => prev.map(o => o.id === orderId ? {...o, status: OrderStatus.CANCELED} : o));
    const order = orders.find(o => o.id === orderId);
    if(order) addLog(LogLevel.WARN, `[ORDER CANCELED] Manually canceled ${order.side} order for ${order.qty} ${order.symbol}.`);
  }, [addLog, orders]);

  // Main Simulation Loop
  useEffect(() => {
    const timer = setInterval(() => {
      const now = Date.now();
      
      // 1. Update Market Prices (Geometric Brownian Motion)
      const dt = TICK_INTERVAL / (252 * 86400 * 1000); // Time step for annualization
      const newMarket = { ...market };
      for (const symbol in newMarket) {
        const ticker = newMarket[symbol];
        const dW = (Math.random() - 0.5) * Math.sqrt(dt);
        const dPrice = ticker.price * (ticker.drift * dt + ticker.volatility * dW);
        ticker.price = Math.max(0.01, ticker.price + dPrice);
        ticker.atr = ticker.atr * 0.998 + (ticker.price * 0.01) * 0.002;
      }
      setMarket(newMarket);

      // 2. Update Positions, Stats, and Equity
      let unrealizedPlTotal = 0;
      setPositions(prev => prev.map(p => {
        const newPrice = newMarket[p.symbol].price;
        const plMultiplier = p.side === OrderSide.BUY ? 1 : -1;
        const newPl = (newPrice - p.avgEntryPrice) * p.qty * plMultiplier;
        unrealizedPlTotal += newPl;
        return { ...p, currentPrice: newPrice, unrealizedPl: newPl, unrealizedPlpc: (newPrice / p.avgEntryPrice - 1) * plMultiplier, marketValue: newPrice * p.qty };
      }));
      
      const currentEquity = equity.current + unrealizedPlTotal;
      const realizedPl = equity.current - INITIAL_EQUITY;
      const currentDailyPl = realizedPl + unrealizedPlTotal;
      setStats(prev => ({ ...prev, dailyPl: currentDailyPl, dailyPlPc: (currentDailyPl / currentEquity) * 100 }));

      // 3. Process Filled Orders
      orders.filter(o => o.status === OrderStatus.FILLED).forEach(order => {
        const fillPrice = order.filledAvgPrice!;
        const existingPosition = positions.find(p => p.symbol === order.symbol);

        if (existingPosition && existingPosition.side !== order.side) {
            const pnl = (fillPrice - existingPosition.avgEntryPrice) * existingPosition.qty * (existingPosition.side === OrderSide.BUY ? 1 : -1);
            if (pnl >= 0) { stats.wins++; totalGrossProfit.current += pnl; } else { stats.losses++; totalGrossLoss.current += Math.abs(pnl); }
            equity.current += pnl;
            addLog(LogLevel.INFO, `[CLOSE] ${existingPosition.symbol}. P/L: $${pnl.toFixed(2)}.`);
            setPositions(prev => prev.filter(p => p.id !== existingPosition.id));
        } else {
            idCounter.current.position++;
            const atr = market[order.symbol].atr;
            const newPosition: Position = {
                id: `pos${idCounter.current.position}`, symbol: order.symbol, qty: order.qty, side: order.side,
                avgEntryPrice: fillPrice, currentPrice: fillPrice, unrealizedPl: 0, unrealizedPlpc: 0,
                marketValue: fillPrice * order.qty,
                takeProfit: order.side === OrderSide.BUY ? fillPrice + (atr * TAKE_PROFIT_ATR_MULT) : fillPrice - (atr * TAKE_PROFIT_ATR_MULT),
                stopLoss: order.side === OrderSide.BUY ? fillPrice - (atr * STOP_LOSS_ATR_MULT) : fillPrice + (atr * STOP_LOSS_ATR_MULT),
            };
            addLog(LogLevel.INFO, `[OPEN] ${newPosition.side.toUpperCase()} ${newPosition.qty} ${newPosition.symbol} @ ${newPosition.avgEntryPrice.toFixed(2)}.`);
            setPositions(prev => [...prev, newPosition]);
            generateTradeAnalysis(order.symbol, order.side, fillPrice, newPosition.takeProfit, newPosition.stopLoss, "EMA Crossover Signal");
        }
        setOrders(prev => prev.filter(o => o.id !== order.id));
      });

      // 4. Update Performance Candles & Indicators
      if (now - candleTimestamp.current > CANDLE_INTERVAL) {
        if (candleTimestamp.current > 0) {
            const { wins, losses } = stats;
            const winRate = (wins + losses) > 0 ? wins / (wins + losses) : 0;
            const profitFactor = totalGrossLoss.current > 0 ? totalGrossProfit.current / totalGrossLoss.current : 0;
            setStats(prev => ({...prev, winRate, profitFactor, wins, losses}));
            const newCandle: PerformanceDataPoint = {
                ...currentCandle.current,
                timestamp: candleTimestamp.current,
                pnl: currentCandle.current.close - INITIAL_EQUITY,
                winRate, profitFactor, wins, losses,
            };
            setPerformanceData(prev => [...prev.slice(-99), newCandle]);
        }
        candleTimestamp.current = now - (now % CANDLE_INTERVAL);
        currentCandle.current = { open: currentEquity, high: currentEquity, low: currentEquity, close: currentEquity };

        // Update EMAs on candle close
        Object.values(newMarket).forEach((ticker: TickerData) => {
            const kShort = 2 / (EMA_SHORT + 1);
            const kLong = 2 / (EMA_LONG + 1);
            ticker.prevEmas = { ...ticker.emas };
            ticker.emas.short = (ticker.price * kShort) + ticker.emas.short * (1 - kShort);
            ticker.emas.long = (ticker.price * kLong) + ticker.emas.long * (1 - kLong);
        });
      } else {
        currentCandle.current.high = Math.max(currentCandle.current.high, currentEquity);
        currentCandle.current.low = Math.min(currentCandle.current.low, currentEquity);
        currentCandle.current.close = currentEquity;
      }
      
      // 5. Check Strategy (EMA Crossover) & TP/SL
      Object.keys(market).forEach((symbol) => {
        const ticker = market[symbol];
        const hasPosition = positions.some(p => p.symbol === symbol);
          if (positions.length < MAX_POSITIONS && !hasPosition) {
              const { emas, prevEmas } = ticker;
              if (prevEmas.short < prevEmas.long && emas.short > emas.long) { // Bullish Crossover
                  const positionSize = Math.floor((equity.current * RISK_PER_TRADE) / (ticker.atr * STOP_LOSS_ATR_MULT));
                  if (positionSize > 0) placeOrder(symbol, OrderSide.BUY, positionSize, `${EMA_SHORT}/${EMA_LONG} Bullish EMA Crossover`);
              } else if (prevEmas.short > prevEmas.long && emas.short < emas.long) { // Bearish Crossover
                  const positionSize = Math.floor((equity.current * RISK_PER_TRADE) / (ticker.atr * STOP_LOSS_ATR_MULT));
                  if (positionSize > 0) placeOrder(symbol, OrderSide.SELL, positionSize, `${EMA_SHORT}/${EMA_LONG} Bearish EMA Crossover`);
              }
          }
      });
      positions.forEach(pos => {
        if ((pos.side === OrderSide.BUY && (pos.currentPrice >= pos.takeProfit || pos.currentPrice <= pos.stopLoss)) ||
            (pos.side === OrderSide.SELL && (pos.currentPrice <= pos.takeProfit || pos.currentPrice >= pos.stopLoss))) {
            closePosition(pos.id, pos.currentPrice >= pos.takeProfit ? "Take Profit" : "Stop Loss");
        }
      });

      // 6. Generate AI Advisories (less frequent)
      if (now - lastAdvisoryTime.current > ADVISORY_INTERVAL) {
        idCounter.current.advisory++;
        const newAdvisory: AdvisoryMessage = {
          id: idCounter.current.advisory, source: Math.random() > 0.5 ? 'Perplexity' : 'OpenRouter',
          symbol: SIMULATED_UNIVERSE[Math.floor(Math.random() * SIMULATED_UNIVERSE.length)],
          content: `Analysis suggests ${Math.random() > 0.5 ? 'bullish continuation' : 'potential reversal pattern'}. Watch key resistance levels.`,
          timestamp: new Date().toISOString()
        }
        setAdvisories(prev => [...prev.slice(-10), newAdvisory]);
        lastAdvisoryTime.current = now;
      }

    }, TICK_INTERVAL);

    return () => clearInterval(timer);
  }, [market, orders, positions, stats.wins, stats.losses, addLog, placeOrder, closePosition, generateTradeAnalysis, cancelOrder]);

  return { stats, performanceData, positions, orders, logs, advisories, tradeAnalyses, closePosition, cancelOrder };
};