import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Bot, User, Sparkles, MessageSquare } from 'lucide-react';
import { PremiumCard } from './ui/PremiumCard';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: number;
}

export function CopilotWidget() {
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState<Message[]>([
        {
            role: 'assistant',
            content: 'Hello! I\'m your AI trading copilot. I can help you analyze the market, review your portfolio, or find trading opportunities. How can I assist you today?',
            timestamp: Date.now(),
        },
    ]);
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Get current system context for better AI responses
    const getSystemContext = async () => {
        try {
            const [accountRes, positionsRes, marketRes, opportunitiesRes] = await Promise.all([
                fetch('http://localhost:8006/account'),
                fetch('http://localhost:8006/positions'),
                fetch('http://localhost:8006/market/status'),
                fetch('http://localhost:8006/scanner/opportunities?limit=10')
            ]);

            const [account, positions, market, opportunities] = await Promise.all([
                accountRes.ok ? accountRes.json() : null,
                positionsRes.ok ? positionsRes.json() : [],
                marketRes.ok ? marketRes.json() : null,
                opportunitiesRes.ok ? opportunitiesRes.json() : []
            ]);

            return {
                account: account ? {
                    equity: account.equity,
                    buying_power: account.buying_power,
                    cash: account.cash,
                    day_trade_count: account.day_trade_count,
                    portfolio_value: account.portfolio_value
                } : null,
                positions: positions.map((p: any) => ({
                    symbol: p.symbol,
                    qty: p.qty,
                    side: p.side,
                    market_value: p.market_value,
                    unrealized_pl: p.unrealized_pl,
                    unrealized_pl_pct: p.unrealized_pl_pct,
                    current_price: p.current_price
                })),
                market_status: market?.isOpen ? 'OPEN' : 'CLOSED',
                opportunities: opportunities.slice(0, 5),
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            console.error('Failed to get system context:', error);
            return null;
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: Date.now(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        try {
            // Get current system context for better AI responses
            const systemContext = await getSystemContext();
            const historyPayload = messages.map(m => ({ role: m.role, content: m.content }));

            // Add timeout to prevent hanging requests
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

            const response = await fetch('http://localhost:8006/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: userMessage.content,
                    history: historyPayload,
                    context: systemContext,
                }),
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!response.ok) throw new Error('Failed to get response');

            const data = await response.json();

            const botMessage: Message = {
                role: 'assistant',
                content: data.response || data.content || 'I received your message but couldn\'t generate a response.',
                timestamp: Date.now(),
            };

            setMessages((prev) => [...prev, botMessage]);
        } catch (error: any) {
            console.error('Chat error:', error);
            let errorContent = 'Sorry, I encountered an error processing your request. Please try again.';
            
            if (error.name === 'AbortError') {
                errorContent = 'Request timed out. Please try a shorter question or try again.';
            }
            
            const errorMessage: Message = {
                role: 'assistant',
                content: errorContent,
                timestamp: Date.now(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    };

    const quickActions = [
        { label: 'My Positions', prompt: 'What are my current positions and how are they performing?' },
        { label: 'Portfolio Review', prompt: 'Review my portfolio performance and risk exposure' },
        { label: 'Top Opportunities', prompt: 'What are the top trading opportunities right now?' },
        { label: 'Market Analysis', prompt: 'Give me a quick market analysis with SPY and VIX trends' },
    ];

    return (
        <PremiumCard
            title="AI Copilot"
            icon={<MessageSquare className="w-5 h-5" />}
            className="h-[600px] flex flex-col"
        >
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2 -mr-2 mb-4">
                <AnimatePresence mode="popLayout">
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ duration: 0.2 }}
                            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            {/* Avatar */}
                            <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${
                                msg.role === 'user'
                                    ? 'bg-primary/20 text-primary'
                                    : 'bg-gradient-to-br from-secondary/20 to-accent/20 text-secondary'
                            }`}>
                                {msg.role === 'user' ? (
                                    <User className="w-4 h-4" />
                                ) : (
                                    <Bot className="w-4 h-4" />
                                )}
                            </div>

                            {/* Message Bubble */}
                            <div className={`max-w-[80%] ${msg.role === 'user' ? 'text-right' : ''}`}>
                                <div className={`inline-block rounded-2xl px-4 py-3 text-sm ${
                                    msg.role === 'user'
                                        ? 'bg-primary text-white rounded-tr-none'
                                        : 'bg-surface border border-glass-border text-text-primary rounded-tl-none'
                                }`}>
                                    <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                                </div>
                                <p className={`text-[10px] text-text-muted mt-1 ${msg.role === 'user' ? 'text-right' : ''}`}>
                                    {new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>

                {/* Loading Indicator */}
                <AnimatePresence>
                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0 }}
                            className="flex gap-3"
                        >
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-secondary/20 to-accent/20 flex items-center justify-center">
                                <Bot className="w-4 h-4 text-secondary" />
                            </div>
                            <div className="bg-surface border border-glass-border rounded-2xl rounded-tl-none px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 text-primary animate-spin" />
                                    <span className="text-sm text-text-secondary">Thinking...</span>
                                </div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                <div ref={messagesEndRef} />
            </div>

            {/* Quick Actions */}
            {messages.length <= 1 && (
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex flex-wrap gap-2 mb-4"
                >
                    {quickActions.map((action, idx) => (
                        <motion.button
                            key={idx}
                            onClick={() => {
                                setInput(action.prompt);
                                inputRef.current?.focus();
                            }}
                            className="px-3 py-1.5 rounded-lg bg-surface border border-glass-border text-xs font-medium text-text-secondary hover:text-white hover:border-primary/30 transition-all flex items-center gap-1.5"
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                        >
                            <Sparkles className="w-3 h-3" />
                            {action.label}
                        </motion.button>
                    ))}
                </motion.div>
            )}

            {/* Input */}
            <form onSubmit={handleSubmit} className="relative">
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Ask about market trends, portfolio analysis..."
                    className="glass-input w-full pr-12"
                    disabled={isLoading}
                />
                <motion.button
                    type="submit"
                    disabled={!input.trim() || isLoading}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg text-primary hover:bg-primary/10 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                >
                    <Send className="w-4 h-4" />
                </motion.button>
            </form>
        </PremiumCard>
    );
}
