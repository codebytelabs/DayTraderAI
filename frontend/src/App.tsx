import { useState } from 'react';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { MarketOverview } from './components/dashboard/MarketOverview';
import { OpportunityFeed } from './components/dashboard/OpportunityFeed';
import { ActivePositions } from './components/dashboard/ActivePositions';
import { SystemStatus } from './components/dashboard/SystemStatus';
import { PortfolioChart } from './components/PortfolioChart';
import { LiveTerminal } from './components/LiveTerminal';
import { CopilotWidget } from './components/CopilotWidget';
import { useMarketData } from './hooks/useMarketData';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const {
    account,
    positions,
    marketStatus,
    opportunities,
    portfolioHistory,
    error
  } = useMarketData();

  return (
    <DashboardLayout activeView={activeView} onNavigate={setActiveView}>
      {activeView === 'dashboard' && (
        <>
          <MarketOverview account={account} marketStatus={marketStatus} />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Column */}
            <div className="lg:col-span-2 space-y-6">
              <PortfolioChart data={portfolioHistory} />
              <ActivePositions positions={positions} />
            </div>

            {/* Side Column */}
            <div className="space-y-6">
              <SystemStatus marketStatus={marketStatus} error={error} />
              <CopilotWidget />
              <OpportunityFeed opportunities={opportunities} />
            </div>
          </div>
        </>
      )}

      {activeView === 'terminal' && (
        <div className="h-[calc(100vh-8rem)]">
          <LiveTerminal />
        </div>
      )}

      {activeView === 'opportunities' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <OpportunityFeed opportunities={opportunities} />
          <CopilotWidget />
        </div>
      )}
    </DashboardLayout>
  );
}

export default App;
