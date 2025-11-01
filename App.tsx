
import React, { useState } from 'react';
import { Dashboard } from './components/Dashboard';
import { Header } from './components/Header';
import { SettingsDrawer } from './components/SettingsDrawer';
import { ConfigProvider } from './state/ConfigContext';
import { TradingProvider } from './state/TradingContext';

const AppShell: React.FC = () => {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <div className="min-h-screen bg-brand-bg font-sans">
      <Header onOpenSettings={() => setSettingsOpen(true)} />
      <main className="p-4 sm:p-6 lg:p-8">
        <Dashboard />
      </main>
      <footer className="text-center p-4 text-brand-text-secondary text-sm">
        <p>Expert Day-Trading Bot — Not Financial Advice. Paper Trading Environment.</p>
      </footer>
      <SettingsDrawer isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ConfigProvider>
      <TradingProvider>
        <AppShell />
      </TradingProvider>
    </ConfigProvider>
  );
};

export default App;
