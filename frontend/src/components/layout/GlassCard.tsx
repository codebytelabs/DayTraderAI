import React from 'react';

interface GlassCardProps {
    children: React.ReactNode;
    className?: string;
    title?: string;
    action?: React.ReactNode;
}

export const GlassCard: React.FC<GlassCardProps> = ({
    children,
    className = '',
    title,
    action
}) => {
    return (
        <div className={`glass-panel p-6 flex flex-col ${className}`}>
            {(title || action) && (
                <div className="flex justify-between items-center mb-4">
                    {title && (
                        <h3 className="text-lg font-semibold text-white tracking-wide">
                            {title}
                        </h3>
                    )}
                    {action && (
                        <div>{action}</div>
                    )}
                </div>
            )}
            <div className="flex-1">
                {children}
            </div>
        </div>
    );
};
