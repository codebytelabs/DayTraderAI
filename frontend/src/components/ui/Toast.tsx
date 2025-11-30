import { Toaster, toast } from 'sonner';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

export function ToastProvider() {
    return (
        <Toaster
            position="top-right"
            expand={false}
            richColors
            closeButton
            toastOptions={{
                style: {
                    background: 'rgba(17, 24, 39, 0.95)',
                    backdropFilter: 'blur(20px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: '#f8fafc',
                    borderRadius: '12px',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                },
                className: 'premium-toast',
            }}
        />
    );
}

// Custom toast functions with icons
export const showToast = {
    success: (message: string, description?: string) => {
        toast.success(message, {
            description,
            icon: <CheckCircle2 className="w-5 h-5 text-success" />,
        });
    },
    error: (message: string, description?: string) => {
        toast.error(message, {
            description,
            icon: <AlertCircle className="w-5 h-5 text-danger" />,
        });
    },
    warning: (message: string, description?: string) => {
        toast.warning(message, {
            description,
            icon: <AlertTriangle className="w-5 h-5 text-warning" />,
        });
    },
    info: (message: string, description?: string) => {
        toast.info(message, {
            description,
            icon: <Info className="w-5 h-5 text-primary" />,
        });
    },
    trade: (symbol: string, action: 'buy' | 'sell', price: number) => {
        const isBuy = action === 'buy';
        toast.custom((t) => (
            <div className="flex items-center gap-3 p-4 bg-surface/95 backdrop-blur-xl border border-glass-border rounded-xl shadow-2xl">
                <div className={`p-2 rounded-lg ${isBuy ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'}`}>
                    {isBuy ? <CheckCircle2 className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                </div>
                <div className="flex-1">
                    <p className="font-semibold text-white">
                        {isBuy ? 'Buy' : 'Sell'} Order Executed
                    </p>
                    <p className="text-sm text-text-secondary">
                        {symbol} @ ${price.toFixed(2)}
                    </p>
                </div>
                <button
                    onClick={() => toast.dismiss(t)}
                    className="p-1 hover:bg-surface rounded-lg text-text-muted hover:text-white transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        ), {
            duration: 5000,
        });
    },
};
