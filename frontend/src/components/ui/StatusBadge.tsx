import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

type BadgeVariant = 'success' | 'danger' | 'warning' | 'primary' | 'neutral';

interface StatusBadgeProps {
  variant?: BadgeVariant;
  children: ReactNode;
  pulse?: boolean;
  icon?: ReactNode;
  size?: 'sm' | 'md' | 'lg';
}

export function StatusBadge({
  variant = 'neutral',
  children,
  pulse = false,
  icon,
  size = 'md',
}: StatusBadgeProps) {
  const variants = {
    success: 'bg-success/15 text-success border-success/30',
    danger: 'bg-danger/15 text-danger border-danger/30',
    warning: 'bg-warning/15 text-warning border-warning/30',
    primary: 'bg-primary/15 text-primary border-primary/30',
    neutral: 'bg-surface text-text-secondary border-glass-border',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-xs',
    lg: 'px-4 py-1.5 text-sm',
  };

  return (
    <motion.span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold border ${variants[variant]} ${sizes[size]}`}
      initial={{ scale: 0.9, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.2 }}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
            variant === 'success' ? 'bg-success' :
            variant === 'danger' ? 'bg-danger' :
            variant === 'warning' ? 'bg-warning' :
            variant === 'primary' ? 'bg-primary' : 'bg-text-secondary'
          }`} />
          <span className={`relative inline-flex rounded-full h-2 w-2 ${
            variant === 'success' ? 'bg-success' :
            variant === 'danger' ? 'bg-danger' :
            variant === 'warning' ? 'bg-warning' :
            variant === 'primary' ? 'bg-primary' : 'bg-text-secondary'
          }`} />
        </span>
      )}
      {icon}
      {children}
    </motion.span>
  );
}

interface TrendBadgeProps {
  value: number;
  suffix?: string;
  showIcon?: boolean;
}

export function TrendBadge({ value, suffix = '%', showIcon = true }: TrendBadgeProps) {
  const isPositive = value >= 0;
  
  return (
    <motion.span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-semibold ${
        isPositive 
          ? 'bg-success/15 text-success' 
          : 'bg-danger/15 text-danger'
      }`}
      initial={{ scale: 0.9 }}
      animate={{ scale: 1 }}
      key={value}
    >
      {showIcon && (
        <svg
          className={`w-3 h-3 ${isPositive ? '' : 'rotate-180'}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
        </svg>
      )}
      {isPositive ? '+' : ''}{value.toFixed(2)}{suffix}
    </motion.span>
  );
}

interface LiveIndicatorProps {
  label?: string;
  variant?: 'success' | 'danger' | 'warning';
}

export function LiveIndicator({ label = 'LIVE', variant = 'success' }: LiveIndicatorProps) {
  const colors = {
    success: 'bg-success',
    danger: 'bg-danger',
    warning: 'bg-warning',
  };

  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2.5 w-2.5">
        <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colors[variant]} opacity-75`} />
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${colors[variant]}`} />
      </span>
      <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
