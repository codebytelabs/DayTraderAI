
import { ChecklistItem, ChecklistStatus } from './types';

export const PAPER_TO_LIVE_CHECKLIST: ChecklistItem[] = [
  {
    category: 'Performance',
    items: [
      { name: 'Trades Min (300)', status: ChecklistStatus.PENDING, details: '127/300 trades' },
      { name: 'Win Rate Min (0.60)', status: ChecklistStatus.PASS, details: '0.63 rolling 200' },
      { name: 'Profit Factor Min (1.50)', status: ChecklistStatus.PASS, details: '1.62 3-month rolling' },
      { name: 'Max Drawdown Max (15%)', status: ChecklistStatus.PASS, details: '11.2% peak-to-trough' },
    ],
  },
  {
    category: 'Execution & Data',
    items: [
      { name: 'Slippage Within Budget', status: ChecklistStatus.PASS, details: 'Avg 8.2bps vs budget' },
      { name: 'Fill Rate Min (95%)', status: ChecklistStatus.PASS, details: '98.7% fill rate' },
      { name: 'No Critical Data Gaps', status: ChecklistStatus.PASS, details: 'Last gap 18 days ago' },
    ],
  },
  {
    category: 'Operations & Risk',
    items: [
      { name: 'Uptime > 99%', status: ChecklistStatus.PASS, details: '30d uptime 99.8%' },
      { name: 'Circuit Breakers Tested', status: ChecklistStatus.PASS, details: 'Last test successful' },
      { name: 'Emergency Runbooks Ready', status: ChecklistStatus.PASS, details: 'All runbooks validated' },
      { name: 'Recovery Drills Passed', status: ChecklistStatus.FAIL, details: 'Last drill failed on DB recon' },
    ],
  },
];
