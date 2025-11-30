import { motion } from 'framer-motion';

interface SkeletonProps {
  className?: string;
  animate?: boolean;
}

export function Skeleton({ className = '', animate = true }: SkeletonProps) {
  return (
    <div
      className={`bg-surface rounded-lg ${animate ? 'animate-shimmer' : ''} ${className}`}
      style={{
        background: animate
          ? 'linear-gradient(90deg, rgba(30, 41, 59, 0.5) 0%, rgba(51, 65, 85, 0.5) 50%, rgba(30, 41, 59, 0.5) 100%)'
          : undefined,
        backgroundSize: '200% 100%',
      }}
    />
  );
}

export function MetricCardSkeleton() {
  return (
    <div className="glass-panel p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <Skeleton className="h-4 w-24 mb-3" />
          <Skeleton className="h-8 w-32 mb-2" />
          <Skeleton className="h-3 w-20" />
        </div>
        <Skeleton className="h-12 w-12 rounded-xl" />
      </div>
    </div>
  );
}

export function TableRowSkeleton({ columns = 6 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="py-4 px-4">
          <Skeleton className="h-4 w-full" />
        </td>
      ))}
    </tr>
  );
}

export function ChartSkeleton({ height = 300 }: { height?: number }) {
  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <Skeleton className="h-5 w-40 mb-2" />
          <Skeleton className="h-3 w-24" />
        </div>
        <div className="flex gap-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-8 w-12 rounded-lg" />
          ))}
        </div>
      </div>
      <div className="w-full rounded-xl bg-surface animate-shimmer" style={{ height }} />
    </div>
  );
}

export function PositionsTableSkeleton() {
  return (
    <div className="glass-panel p-6">
      <div className="flex items-center justify-between mb-6">
        <Skeleton className="h-6 w-36" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <div className="space-y-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-4 py-3 border-b border-glass-border/30">
            <Skeleton className="h-10 w-10 rounded-lg" />
            <div className="flex-1">
              <Skeleton className="h-4 w-20 mb-2" />
              <Skeleton className="h-3 w-12" />
            </div>
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        ))}
      </div>
    </div>
  );
}

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function Spinner({ size = 'md', className = '' }: SpinnerProps) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <motion.div
      className={`${sizes[size]} ${className}`}
      animate={{ rotate: 360 }}
      transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
    >
      <svg viewBox="0 0 24 24" fill="none" className="w-full h-full">
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
          className="opacity-20"
        />
        <path
          d="M12 2a10 10 0 0 1 10 10"
          stroke="currentColor"
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>
    </motion.div>
  );
}

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Loading...' }: LoadingOverlayProps) {
  return (
    <motion.div
      className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="flex flex-col items-center gap-4">
        <Spinner size="lg" className="text-primary" />
        <p className="text-sm text-text-secondary">{message}</p>
      </div>
    </motion.div>
  );
}

export function PulsingDot({ color = 'primary' }: { color?: 'primary' | 'success' | 'danger' | 'warning' }) {
  const colors = {
    primary: 'bg-primary',
    success: 'bg-success',
    danger: 'bg-danger',
    warning: 'bg-warning',
  };

  return (
    <span className="relative flex h-3 w-3">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colors[color]} opacity-75`} />
      <span className={`relative inline-flex rounded-full h-3 w-3 ${colors[color]}`} />
    </span>
  );
}
