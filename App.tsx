
import React from 'react';
import { Dashboard } from './components/Dashboard';
import { Header } from './components/Header';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-brand-bg font-sans">
      <Header />
      <main className="p-4 sm:p-6 lg:p-8">
        <Dashboard />
      </main>
      <footer className="text-center p-4 text-brand-text-secondary text-sm">
        <p>Expert Day-Trading Bot — Not Financial Advice. Paper Trading Environment.</p>
      </footer>
    </div>
  );
};

export default App;
