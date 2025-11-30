import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface PremiumCardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
  icon?: ReactNode;
  variant?: 'default' | 'elevated' | 'glow';
  animate?: boolean;
}

export function PremiumCard({
  children,
  className = '',
  title,
  subtitle,
  action,
  icon,
  variant = 'default',
  animate = true,
}: PremiumCardProps) {
  const variants = {
    default: 'glass-panel',
    elevated: 'glass-card-elevated',
    glow: 'glass-panel hover:shadow-[0_0_30px_rgba(59,130,246,0.15)]',
  };

  const content = (
    <div className={`${variants[variant]} p-6 ${className}`}>
      {(title || action || icon) && (
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            {icon && (
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary/20 to-secondary/20 text-primary">
                {icon}
              </div>
            )}
            <div>
              {title && (
                <h3 className="text-lg font-semibold text-white tracking-tight">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-sm text-text-secondary mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
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

interface MetricCardProps {
  label: string;
  value: ReactNode;
  change?: ReactNode;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export function MetricCard({
  label,
  value,
  change,
  icon,
  trend = 'neutral',
  className = '',
}: MetricCardProps) {
  const trendColors = {
    up: 'text-success',
    down: 'text-danger',
    neutral: 'text-text-secondary',
  };

  const trendBg = {
    up: 'bg-success/10 text-success',
    down: 'bg-danger/10 text-danger',
    neutral: 'bg-surface text-text-secondary',
  };

  return (
    <motion.div
      className={`glass-panel p-5 ${className}`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-text-secondary mb-2">{label}</p>
          <div className={`text-2xl font-bold ${trend === 'up' ? 'text-success glow-success' : trend === 'down' ? 'text-danger glow-danger' : 'text-white'}`}>
            {value}
          </div>
          {change && (
            <div className={`mt-2 text-sm font-medium ${trendColors[trend]}`}>
              {change}
            </div>
          )}
        </div>
        {icon && (
          <div className={`p-3 rounded-xl ${trendBg[trend]}`}>
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  icon: ReactNode;
  color?: 'primary' | 'success' | 'danger' | 'warning' | 'accent';
}

export function StatCard({ label, value, subValue, icon, color = 'primary' }: StatCardProps) {
  const colorClasses = {
    primary: 'from-primary/20 to-primary/5 text-primary border-primary/20',
    success: 'from-success/20 to-success/5 text-success border-success/20',
    danger: 'from-danger/20 to-danger/5 text-danger border-danger/20',
    warning: 'from-warning/20 to-warning/5 text-warning border-warning/20',
    accent: 'from-accent/20 to-accent/5 text-accent border-accent/20',
  };

  return (
    <motion.div
      className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${colorClasses[color]} border p-5`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-text-secondary mb-1">{label}</p>
          <p className="text-2xl font-bold text-white metric-value">{value}</p>
          {subValue && (
            <p className="text-xs text-text-muted mt-1">{subValue}</p>
          )}
        </div>
        <div className="p-2 rounded-lg bg-white/5">
          {icon}
        </div>
      </div>
      
      {/* Decorative gradient orb */}
      <div className="absolute -right-4 -bottom-4 w-24 h-24 rounded-full bg-current opacity-10 blur-2xl" />
    </motion.div>
  );
}
