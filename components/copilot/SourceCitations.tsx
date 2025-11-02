import React, { useState } from 'react';

export interface Source {
  title: string;
  url: string;
  snippet?: string;
}

interface SourceCitationsProps {
  sources: Source[];
  className?: string;
}

export const SourceCitations: React.FC<SourceCitationsProps> = ({ sources, className = '' }) => {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className={`mt-3 ${className}`}>
      <h5 className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2">Sources:</h5>
      <div className="space-y-1">
        {sources.map((source, index) => (
          <div
            key={index}
            className="relative"
            onMouseEnter={() => setHoveredIndex(index)}
            onMouseLeave={() => setHoveredIndex(null)}
          >
            <a
              href={source.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1"
            >
              <span className="font-mono text-gray-500 dark:text-gray-400">[{index + 1}]</span>
              <span>{source.title}</span>
              <svg
                className="w-3 h-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
            </a>

            {/* Tooltip with snippet */}
            {source.snippet && hoveredIndex === index && (
              <div className="absolute z-10 left-0 top-full mt-1 w-64 p-2 bg-gray-900 dark:bg-gray-800 text-white text-xs rounded-md shadow-lg border border-gray-700">
                <div className="line-clamp-3">{source.snippet}</div>
                <div className="absolute -top-1 left-4 w-2 h-2 bg-gray-900 dark:bg-gray-800 border-l border-t border-gray-700 transform rotate-45" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
