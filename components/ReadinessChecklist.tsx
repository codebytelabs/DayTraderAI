
import React from 'react';
import { ChecklistItem, ChecklistStatus } from '../types';
import { PAPER_TO_LIVE_CHECKLIST } from '../constants';
import { CheckCircleIcon } from './icons/CheckCircleIcon';
import { XCircleIcon } from './icons/XCircleIcon';
import { ClockIcon } from './icons/ClockIcon';

const StatusIcon: React.FC<{ status: ChecklistStatus }> = ({ status }) => {
  switch (status) {
    case ChecklistStatus.PASS:
      return <CheckCircleIcon className="w-5 h-5 text-brand-success" />;
    case ChecklistStatus.FAIL:
      return <XCircleIcon className="w-5 h-5 text-brand-danger" />;
    case ChecklistStatus.PENDING:
      return <ClockIcon className="w-5 h-5 text-brand-warning" />;
    default:
      return null;
  }
};

export const ReadinessChecklist: React.FC = () => {
  const checklist: ChecklistItem[] = PAPER_TO_LIVE_CHECKLIST;

  return (
    <div className="bg-brand-surface p-4 rounded-lg shadow-lg border border-brand-surface-2">
      <h3 className="text-lg font-semibold text-brand-text mb-4">Paper → Live Readiness</h3>
      <div className="space-y-4">
        {checklist.map((categoryItem) => (
          <div key={categoryItem.category}>
            <h4 className="text-sm font-bold text-brand-text-secondary mb-2">{categoryItem.category}</h4>
            <ul className="space-y-2">
              {categoryItem.items.map((item) => (
                <li key={item.name} className="flex items-start justify-between text-sm">
                  <div className="flex items-center">
                    <StatusIcon status={item.status} />
                    <span className="ml-2 text-brand-text">{item.name}</span>
                  </div>
                  <span className="text-xs text-brand-text-secondary text-right ml-2">{item.details}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};
