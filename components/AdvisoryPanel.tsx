
import React from 'react';
import { AdvisoryMessage } from '../types';

interface AdvisoryPanelProps {
  advisories: AdvisoryMessage[];
}

export const AdvisoryPanel: React.FC<AdvisoryPanelProps> = ({ advisories }) => {
  const recentAdvisories = advisories.slice(-5).reverse();

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Advisory Feed</h3>
      <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
        {recentAdvisories.length > 0 ? recentAdvisories.map((advisory) => (
          <div key={advisory.id} className="text-sm p-3 bg-brand-surface-2 rounded-md">
            <div className="flex justify-between items-center mb-1">
              <span className={`font-bold ${advisory.source === 'Perplexity' ? 'text-purple-400' : 'text-indigo-400'}`}>
                {advisory.source} {advisory.symbol && `(${advisory.symbol})`}
              </span>
              <span className="text-xs text-brand-text-secondary">
                {new Date(advisory.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-brand-text-secondary">{advisory.content}</p>
          </div>
        )) : (
          <div className="text-center py-4 text-brand-text-secondary text-sm">No advisories yet.</div>
        )}
      </div>
    </div>
  );
};
