import React from 'react';
import { OrderSide } from '../../types';

export interface TradeRecommendation {
  action: 'buy' | 'sell';
  symbol: string;
  entry: number;
  takeProfit: number;
  stopLoss: number;
  positionSize: number;
  riskReward: number;
}

interface TradeRecommendationCardProps {
  recommendation: TradeRecommendation;
  onExecute?: (rec: TradeRecommendation) => void;
  tradeExecutionEnabled?: boolean;
  className?: string;
}

export const TradeRecommendationCard: React.FC<TradeRecommendationCardProps> = ({
  recommendation,
  onExecute,
  tradeExecutionEnabled = false,
  className = '',
}) => {
  const { action, symbol, entry, takeProfit, stopLoss, positionSize, riskReward } = recommendation;

  const profitPct = ((takeProfit - entry) / entry) * 100;
  const lossPct = ((entry - stopLoss) / entry) * 100;

  const actionColor = action === 'buy' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400';
  const actionBg = action === 'buy' ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20';

  return (
    <div className={`rounded-lg border border-gray-200 dark:border-gray-700 ${actionBg} p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <h4 className={`text-lg font-bold ${actionColor}`}>
          {action.toUpperCase()} {symbol}
        </h4>
        <span className="text-xs text-gray-500 dark:text-gray-400">
          R:R 1:{riskReward.toFixed(2)}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Entry</div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            ${entry.toFixed(2)}
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Position Size</div>
          <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {positionSize} shares
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Target</div>
          <div className="text-sm font-semibold text-green-600 dark:text-green-400">
            ${takeProfit.toFixed(2)} (+{profitPct.toFixed(2)}%)
          </div>
        </div>

        <div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Stop</div>
          <div className="text-sm font-semibold text-red-600 dark:text-red-400">
            ${stopLoss.toFixed(2)} (-{lossPct.toFixed(2)}%)
          </div>
        </div>
      </div>

      {tradeExecutionEnabled && onExecute && (
        <button
          onClick={() => onExecute(recommendation)}
          className={`w-full py-2 px-4 rounded-md font-semibold text-white transition-colors ${
            action === 'buy'
              ? 'bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600'
              : 'bg-red-600 hover:bg-red-700 dark:bg-red-500 dark:hover:bg-red-600'
          }`}
        >
          Execute Trade
        </button>
      )}
    </div>
  );
};
