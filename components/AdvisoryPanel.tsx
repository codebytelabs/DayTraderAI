
import React from 'react';
import { AdvisoryMessage } from '../types';
import { MarkdownRenderer } from './MarkdownRenderer';

interface AdvisoryPanelProps {
  advisories: AdvisoryMessage[];
}

export const AdvisoryPanel: React.FC<AdvisoryPanelProps> = ({ advisories }) => {
  const recentAdvisories = advisories.slice(-5).reverse();

  return (
    <div className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 backdrop-blur-sm p-6 rounded-xl shadow-xl border border-slate-700/50">
      <div className="flex items-center gap-2 mb-5">
        <span className="text-xl">📡</span>
        <h3 className="text-xl font-bold text-white">Advisory Feed</h3>
      </div>
      <div className="space-y-3 max-h-80 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
        {recentAdvisories.length > 0 ? recentAdvisories.map((advisory) => (
          <div key={advisory.id} className="text-sm p-4 bg-slate-900/50 rounded-lg border border-slate-700/30 hover:border-slate-600/50 transition-all">
            <div className="flex justify-between items-start mb-2">
              <div className="flex items-center gap-2">
                <span className={`font-bold text-sm ${
                  advisory.source === 'Perplexity' ? 'text-purple-400' : 'text-indigo-400'
                }`}>
                  {advisory.source}
                </span>
                {advisory.symbol && (
                  <span className="px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs font-semibold">
                    {advisory.symbol}
                  </span>
                )}
              </div>
              <span className="text-xs text-slate-500">
                {new Date(advisory.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <div className="text-slate-300 leading-relaxed">
              <MarkdownRenderer content={advisory.content} />
            </div>
          </div>
        )) : (
          <div className="text-center py-12 text-slate-500">
            <div className="flex flex-col items-center gap-2">
              <span className="text-3xl">📭</span>
              <span>No advisories yet</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
