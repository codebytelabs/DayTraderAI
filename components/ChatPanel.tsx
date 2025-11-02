import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { nanoid } from 'nanoid/non-secure';
import { OrderSide } from '../types';
import { useTrading } from '../state/TradingContext';
import { useConfig } from '../state/ConfigContext';
import { CopilotMessage, CopilotResult, invokeCopilot } from '../services/copilot';
import { MarkdownRenderer } from './MarkdownRenderer';

type ConversationMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  provider?: string;
  meta?: {
    route?: CopilotResult['route'];
    notes?: string[];
    confidence?: number;
    highlights?: string[];
    citations?: unknown[];
  };
};

const timestamp = () => new Date().toISOString();

const COMMAND_HELP = [
  '`close all positions` – flatten the book',
  '`close <symbol>` – close a single position (e.g., "close NVDA")',
  '`cancel order <id>` – cancel by order id',
  '`cancel orders for <symbol>` – cancel all orders for a ticker',
  '`buy|sell <qty> <symbol>` – place a simulated market order (e.g., "buy 50 AAPL")',
  '`status` – quick summary of current performance',
];

export const ChatPanel: React.FC = () => {
  const trading = useTrading();
  const { config } = useConfig();
  const [messages, setMessages] = useState<ConversationMessage[]>(() => [
    {
      id: nanoid(),
      role: 'assistant',
      content:
        'Hi! I am the DayTraderAI ops copilot. I know the watchlist, risk settings, live positions, orders, logs, and advisories. Ask for a status update, request a recap, or instruct me to close/cancel trades. Provide API keys in Settings to enable full LLM explanations.',
      timestamp: timestamp(),
      provider: 'System',
    },
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setProcessing] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [messages]);

  const buildContext = useCallback(() => {
    const summary = trading.getStateSummary();
    const snapshot = trading.getStateSnapshot();
    const lines: string[] = [
      `Summary: ${summary}`,
      `Watchlist: ${snapshot.watchlist?.join(', ') ?? 'n/a'}`,
      `Risk caps: max ${trading.riskSettings.maxPositions} positions, ${(
        trading.riskSettings.riskPerTradePct * 100
      ).toFixed(2)}% per trade`,
      '',
      'Open Positions:',
      snapshot.positions.length
        ? snapshot.positions
            .map(
              (pos) =>
                `${pos.symbol} ${pos.side.toUpperCase()} ${pos.qty} @ ${pos.avgEntryPrice.toFixed(
                  2,
                )} | Px ${pos.currentPrice.toFixed(2)} | P/L ${pos.unrealizedPl.toFixed(2)}`,
            )
            .join('\n')
        : 'None',
      '',
      'Pending Orders:',
      snapshot.orders.length
        ? snapshot.orders
            .map(
              (order) =>
                `${order.id} ${order.side.toUpperCase()} ${order.qty} ${order.symbol} status=${order.status}`,
            )
            .join('\n')
        : 'None',
      '',
      'Latest Logs:',
      snapshot.logs.slice(-5).map((log) => `${log.timestamp} [${log.level}] ${log.message}`).join('\n') || 'None',
      '',
      'Advisories:',
      snapshot.advisories
        .slice(-5)
        .map((advisory) => `${advisory.timestamp} ${advisory.source}: ${advisory.content}`)
        .join('\n') || 'None',
    ];
    return lines.join('\n');
  }, [trading]);

  const appendMessage = useCallback(
    (message: ConversationMessage) => {
      setMessages((prev) => [...prev, message]);
    },
    [setMessages],
  );

  const runLocalCommand = useCallback(
    (prompt: string): string[] => {
      const feedback: string[] = [];
      const text = prompt.toLowerCase();

      if (/help/.test(text)) {
        feedback.push('Available commands:\n' + COMMAND_HELP.join('\n'));
      }
      if (/status|summary|recap/.test(text)) {
        feedback.push(trading.getStateSummary());
      }
      if (/close all (positions)?/.test(text)) {
        if (trading.positions.length === 0) {
          feedback.push('No open positions to close.');
        } else {
          trading.positions.forEach((pos) => trading.closePosition(pos.id, 'Chat command: close all'));
          feedback.push(`Flattened ${trading.positions.length} open position(s).`);
        }
      }

      const closeMatch = prompt.match(/close(?: position)? ([A-Za-z]{1,6})/i);
      if (closeMatch) {
        const symbol = closeMatch[1].toUpperCase();
        const target = trading.positions.find((pos) => pos.symbol === symbol);
        if (target) {
          trading.closePosition(target.id, `Chat command: close ${symbol}`);
          feedback.push(`Closing ${symbol} position (${target.side} ${target.qty}).`);
        } else {
          feedback.push(`No open position found for ${symbol}.`);
        }
      }

      const cancelBySymbol = prompt.match(/cancel orders? for ([A-Za-z]{1,6})/i);
      if (cancelBySymbol) {
        const symbol = cancelBySymbol[1].toUpperCase();
        const matchedOrders = trading.orders.filter((order) => order.symbol === symbol);
        if (matchedOrders.length) {
          matchedOrders.forEach((order) => trading.cancelOrder(order.id));
          feedback.push(`Cancelling ${matchedOrders.length} order(s) for ${symbol}.`);
        } else {
          feedback.push(`No pending orders found for ${symbol}.`);
        }
      }

      const cancelById = prompt.match(/cancel order ([A-Za-z0-9-]+)/i);
      if (cancelById) {
        const orderId = cancelById[1];
        const order = trading.orders.find((o) => o.id.toLowerCase() === orderId.toLowerCase());
        if (order) {
          trading.cancelOrder(order.id);
          feedback.push(`Cancelling order ${order.id}.`);
        } else {
          feedback.push(`Could not find order with id ${orderId}.`);
        }
      }

      const manualOrder = prompt.match(/\b(buy|sell)\s+(\d+)\s+([A-Za-z]{1,6})\b/i);
      if (manualOrder) {
        const side = manualOrder[1].toLowerCase() === 'buy' ? OrderSide.BUY : OrderSide.SELL;
        const qty = parseInt(manualOrder[2], 10);
        const symbol = manualOrder[3].toUpperCase();
        if (Number.isFinite(qty) && qty > 0) {
          trading.placeOrder(symbol, side, qty, `Chat command: ${manualOrder[0]}`);
          feedback.push(`Submitted ${side.toUpperCase()} order for ${qty} ${symbol}.`);
        } else {
          feedback.push('Order quantity must be a positive number.');
        }
      }

      return feedback;
    },
    [trading],
  );

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage: ConversationMessage = {
      id: nanoid(),
      role: 'user',
      content: trimmed,
      timestamp: timestamp(),
    };
    appendMessage(userMessage);
    setInput('');
    setProcessing(true);

    const commandResponses = runLocalCommand(trimmed);
    if (commandResponses.length) {
      appendMessage({
        id: nanoid(),
        role: 'assistant',
        content: commandResponses.join('\n'),
        timestamp: timestamp(),
        provider: 'Automation',
      });
    }

    try {
      const context = buildContext();
      const history: CopilotMessage[] = messages
        .concat(userMessage)
        .slice(-6)
        .map(({ role, content }) => ({ role, content } as CopilotMessage));
      const result = await invokeCopilot({
        prompt: trimmed,
        context,
        history,
      });
      const meta = {
        route: result.route,
        notes: result.notes,
        confidence: result.confidence,
        highlights: result.highlights,
        citations: result.citations,
      };
      appendMessage({
        id: nanoid(),
        role: 'assistant',
        content: result.content,
        timestamp: timestamp(),
        provider: result.provider,
        meta,
      });
    } catch (error) {
      console.error(error);
      appendMessage({
        id: nanoid(),
        role: 'assistant',
        content: `Something went wrong while talking to the copilot: ${(error as Error).message}`,
        timestamp: timestamp(),
        provider: 'Error',
      });
    } finally {
      setProcessing(false);
    }
  };

  const providerHint = useMemo(() => {
    if (config.chat.provider === 'none') {
      return 'Copilot context ready, but LLM integration disabled — responses will use local summaries.';
    }
    return 'Copilot uses backend-managed hybrid routing with market research + strategy analysis.';
  }, [config.chat.provider]);

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2 h-[460px] flex flex-col">
      <header className="mb-3">
        <h3 className="text-lg font-semibold text-brand-text">Ops Copilot</h3>
        <p className="text-xs text-brand-text-secondary">
          Conversational control centre. Type `help` for supported commands.
        </p>
        {providerHint && <p className="text-xs text-brand-warning mt-1">{providerHint}</p>}
      </header>
      <div ref={containerRef} className="flex-1 overflow-y-auto space-y-3 pr-1">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`rounded-md px-3 py-2 text-sm whitespace-pre-wrap ${
              message.role === 'user' ? 'bg-brand-accent/20 text-brand-text' : 'bg-brand-surface-2 text-brand-text'
            }`}
          >
            <div className="flex items-center justify-between text-xs text-brand-text-secondary mb-1">
              <span>
                {message.role === 'user' ? 'You' : message.provider ?? 'Copilot'}
                {message.role === 'assistant' && typeof message.meta?.confidence === 'number'
                  ? ` · ${(message.meta.confidence * 100).toFixed(0)}% confidence`
                  : ''}
              </span>
              <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
            </div>
            <div>
              {message.role === 'assistant' ? (
                <MarkdownRenderer content={message.content} />
              ) : (
                message.content
              )}
            </div>
            {message.role === 'assistant' && message.meta?.route && (
              <div className="mt-2 text-xs text-brand-text-secondary space-y-1">
                <div>
                  Route: {message.meta.route.category}{' '}
                  {message.meta.route.targets.length
                    ? `→ ${message.meta.route.targets.join(', ')}`
                    : ''}
                </div>
                {message.meta.notes && message.meta.notes.length > 0 && (
                  <div>Notes: {message.meta.notes.join(' | ')}</div>
                )}
                {message.meta.citations && message.meta.citations.length > 0 && (
                  <div className="space-y-1">
                    <div>Citations:</div>
                    <ul className="list-disc list-inside">
                      {message.meta.citations.map((citation, index) => {
                        if (typeof citation === 'string') {
                          return <li key={index}>{citation}</li>;
                        }
                        if (citation && typeof citation === 'object') {
                          const url = (citation as { url?: string }).url;
                          const title = (citation as { title?: string }).title || url;
                          return (
                            <li key={index}>
                              {url ? (
                                <a
                                  href={url}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-brand-accent hover:underline"
                                >
                                  {title || url}
                                </a>
                              ) : (
                                title || 'Citation'
                              )}
                            </li>
                          );
                        }
                        return <li key={index}>{String(citation)}</li>;
                      })}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSubmit} className="mt-3 flex items-center space-x-2">
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about status, close trades, or plan next steps..."
          className="flex-1 px-3 py-2 rounded-md bg-brand-surface-2 border border-brand-surface-2 text-brand-text focus:outline-none focus:ring-2 focus:ring-brand-accent"
        />
        <button
          type="submit"
          disabled={isProcessing}
          className="px-3 py-2 bg-brand-accent hover:bg-brand-accent-hover rounded-md text-sm font-semibold disabled:opacity-50"
        >
          {isProcessing ? 'Thinking…' : 'Send'}
        </button>
      </form>
    </div>
  );
};
