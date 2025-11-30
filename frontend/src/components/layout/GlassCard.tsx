import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface GlassCardProps {
    children: ReactNode;
    className?: string;
    title?: string;
    action?: ReactNode;
    animate?: boolean;
}

export function GlassCard({
    children,
    className = '',
    title,
    action,
    animate = true
}: GlassCardProps) {
    const content = (
        <div className={`glass-panel p-6 ${className}`}>
            {(title || action) && (
                <div className="flex justify-between items-center mb-4">
                    {title && (
                        <h3 className="text-lg font-semibold text-white tracking-tight">
                            {title}
                        </h3>
                    )}
                    {action && <div>{action}</div>}
                </div>
            )}
            {children}
        </div>
    );

    if (!animate) return content;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.4, 0, 0.2, 1] }}
        >
            {content}
        </motion.div>
    );
}
