import React from 'react';

interface ConfidenceIndicatorProps {
  score: number; // 0-1 range
  className?: string;
}

export const ConfidenceIndicator: React.FC<ConfidenceIndicatorProps> = ({
  score,
  className = '',
}) => {
  const getLevel = () => {
    if (score >= 0.8) return 'high';
    if (score >= 0.6) return 'medium';
    return 'low';
  };

  const level = getLevel();
  const percentage = Math.round(score * 100);

  const colors = {
    high: {
      bg: 'bg-green-100 dark:bg-green-900',
      fill: 'bg-green-500',
      text: 'text-green-800 dark:text-green-200',
    },
    medium: {
      bg: 'bg-yellow-100 dark:bg-yellow-900',
      fill: 'bg-yellow-500',
      text: 'text-yellow-800 dark:text-yellow-200',
    },
    low: {
      bg: 'bg-red-100 dark:bg-red-900',
      fill: 'bg-red-500',
      text: 'text-red-800 dark:text-red-200',
    },
  };

  const config = colors[level];

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`flex-1 h-2 rounded-full ${config.bg} overflow-hidden`}>
        <div
          className={`h-full ${config.fill} transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className={`text-xs font-medium ${config.text} min-w-[3rem] text-right`}>
        {percentage}%
      </span>
    </div>
  );
};
