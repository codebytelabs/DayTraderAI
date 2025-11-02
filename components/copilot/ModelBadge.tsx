import React from 'react';

export type AIModel = 'perplexity' | 'openrouter' | 'chained' | 'system';

interface ModelBadgeProps {
  model: AIModel;
  className?: string;
}

export const ModelBadge: React.FC<ModelBadgeProps> = ({ model, className = '' }) => {
  const badges = {
    perplexity: {
      icon: '🔍',
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      label: 'Research',
    },
    openrouter: {
      icon: '🧠',
      color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
      label: 'Analysis',
    },
    chained: {
      icon: '🔗',
      color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      label: 'Deep Analysis',
    },
    system: {
      icon: '⚙️',
      color: 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200',
      label: 'System',
    },
  };

  const badge = badges[model] || badges.system;

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${badge.color} ${className}`}
    >
      <span>{badge.icon}</span>
      <span>{badge.label}</span>
    </span>
  );
};
