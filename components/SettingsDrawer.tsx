import React, { useMemo, useState } from 'react';
import { AppConfig, LLMProvider, useConfig } from '../state/ConfigContext';

interface SettingsDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

type SectionKey = 'api' | 'strategy' | 'chat';

const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement>> = (props) => (
  <input
    {...props}
    className={`w-full px-3 py-2 rounded-md bg-brand-surface-2 border border-brand-surface-2 text-brand-text focus:outline-none focus:ring-2 focus:ring-brand-accent ${props.className ?? ''}`}
  />
);

const SectionToggle: React.FC<{ section: SectionKey; active: SectionKey; onChange: (section: SectionKey) => void }> = ({
  section,
  active,
  onChange,
}) => {
  const labels: Record<SectionKey, string> = {
    api: 'API Keys & Services',
    strategy: 'Strategy & Risk',
    chat: 'Copilot & Automation',
  };
  return (
    <button
      type="button"
      onClick={() => onChange(section)}
      className={`text-left px-4 py-2 rounded-md transition ${
        active === section ? 'bg-brand-accent text-white' : 'bg-transparent text-brand-text-secondary hover:text-brand-text'
      }`}
    >
      {labels[section]}
    </button>
  );
};

export const SettingsDrawer: React.FC<SettingsDrawerProps> = ({ isOpen, onClose }) => {
  const { config, updateConfig, resetConfig } = useConfig();
  const [activeSection, setActiveSection] = useState<SectionKey>('api');
  const [form, setForm] = useState<AppConfig>(config);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  React.useEffect(() => {
    if (isOpen) {
      setForm(config);
      setStatusMessage(null);
    }
  }, [config, isOpen]);

  const handleChange = (section: keyof AppConfig, key: string, value: string | number) => {
    setForm((prev) => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: typeof value === 'string' ? value : Number(value),
      },
    }));
  };

  const saveChanges = () => {
    updateConfig(form);
    setStatusMessage('Configuration saved. Changes apply immediately.');
  };

  const reset = () => {
    resetConfig();
    setStatusMessage('Configuration reset to defaults.');
  };

  const providers: { value: LLMProvider; label: string }[] = useMemo(
    () => [
      { value: 'openrouter', label: 'OpenRouter (multi-model gateway)' },
      { value: 'perplexity', label: 'Perplexity (news + chat)' },
      { value: 'none', label: 'Disabled (manual only)' },
    ],
    [],
  );

  return (
    <div
      className={`fixed inset-0 z-50 transition ${
        isOpen ? 'pointer-events-auto' : 'pointer-events-none'
      }`}
      aria-hidden={!isOpen}
    >
      <div
        className={`absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity ${isOpen ? 'opacity-100' : 'opacity-0'}`}
        onClick={onClose}
      />
      <aside
        className={`absolute right-0 top-0 h-full w-full sm:w-[480px] bg-brand-bg border-l border-brand-surface-2 shadow-2xl transform transition-transform duration-300 ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <header className="flex items-center justify-between px-6 py-5 border-b border-brand-surface-2">
          <div>
            <h2 className="text-xl font-semibold text-brand-text">System Settings</h2>
            <p className="text-sm text-brand-text-secondary">Personal keys stay local via browser storage.</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-brand-text-secondary hover:text-brand-text transition"
          >
            ✕
          </button>
        </header>

        <div className="flex h-[calc(100%-140px)]">
          <nav className="w-48 border-r border-brand-surface-2 px-2 py-4 space-y-2">
            <SectionToggle section="api" active={activeSection} onChange={setActiveSection} />
            <SectionToggle section="strategy" active={activeSection} onChange={setActiveSection} />
            <SectionToggle section="chat" active={activeSection} onChange={setActiveSection} />
          </nav>

          <form className="flex-1 overflow-y-auto px-6 py-6 space-y-6" onSubmit={(e) => e.preventDefault()}>
            {activeSection === 'api' && (
              <>
                <section>
                  <h3 className="text-lg font-semibold mb-3 text-brand-text">Alpaca</h3>
                  <div className="space-y-3">
                    <Input
                      value={form.alpaca.baseUrl}
                      onChange={(event) => handleChange('alpaca', 'baseUrl', event.target.value)}
                      placeholder="https://paper-api.alpaca.markets/v2"
                    />
                    <Input
                      value={form.alpaca.key}
                      onChange={(event) => handleChange('alpaca', 'key', event.target.value)}
                      placeholder="API Key"
                    />
                    <Input
                      value={form.alpaca.secret}
                      onChange={(event) => handleChange('alpaca', 'secret', event.target.value)}
                      placeholder="API Secret"
                    />
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-semibold mb-3 text-brand-text">Supabase</h3>
                  <div className="space-y-3">
                    <Input
                      value={form.supabase.url}
                      onChange={(event) => handleChange('supabase', 'url', event.target.value)}
                      placeholder="https://xyzcompany.supabase.co"
                    />
                    <Input
                      value={form.supabase.anonKey}
                      onChange={(event) => handleChange('supabase', 'anonKey', event.target.value)}
                      placeholder="Anon Key"
                    />
                    <Input
                      value={form.supabase.serviceRoleKey}
                      onChange={(event) => handleChange('supabase', 'serviceRoleKey', event.target.value)}
                      placeholder="Service Role Key"
                    />
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-semibold mb-3 text-brand-text">Perplexity</h3>
                  <div className="space-y-3">
                    <Input
                      value={form.perplexity.apiKey}
                      onChange={(event) => handleChange('perplexity', 'apiKey', event.target.value)}
                      placeholder="Perplexity API Key"
                    />
                    <Input
                      value={form.perplexity.model}
                      onChange={(event) => handleChange('perplexity', 'model', event.target.value)}
                      placeholder="sonar-pro"
                    />
                  </div>
                </section>

                <section>
                  <h3 className="text-lg font-semibold mb-3 text-brand-text">OpenRouter</h3>
                  <div className="space-y-3">
                    <Input
                      value={form.openRouter.apiKey}
                      onChange={(event) => handleChange('openRouter', 'apiKey', event.target.value)}
                      placeholder="OpenRouter API Key"
                    />
                    <Input
                      value={form.openRouter.model}
                      onChange={(event) => handleChange('openRouter', 'model', event.target.value)}
                      placeholder="openai/gpt-4.1-mini"
                    />
                    <Input
                      value={form.openRouter.fallbackModel}
                      onChange={(event) => handleChange('openRouter', 'fallbackModel', event.target.value)}
                      placeholder="Fallback Model"
                    />
                  </div>
                </section>
              </>
            )}

            {activeSection === 'strategy' && (
              <>
                <section>
                  <h3 className="text-lg font-semibold mb-3 text-brand-text">Watchlist & Risk</h3>
                  <div className="space-y-3">
                    <Input
                      value={form.strategy.watchlist}
                      onChange={(event) => handleChange('strategy', 'watchlist', event.target.value)}
                      placeholder="SPY,QQQ,AAPL..."
                    />
                    <label className="block text-sm text-brand-text-secondary">
                      Risk Per Trade (%)
                      <Input
                        type="number"
                        step="0.001"
                        value={form.strategy.riskPerTradePct}
                        onChange={(event) => handleChange('strategy', 'riskPerTradePct', event.target.value)}
                      />
                    </label>
                    <label className="block text-sm text-brand-text-secondary">
                      Max Concurrent Positions
                      <Input
                        type="number"
                        value={form.strategy.maxPositions}
                        onChange={(event) => handleChange('strategy', 'maxPositions', event.target.value)}
                      />
                    </label>
                  </div>
                </section>
              </>
            )}

            {activeSection === 'chat' && (
              <section className="space-y-3">
                <h3 className="text-lg font-semibold text-brand-text">Copilot & Automation</h3>
                <label className="block text-sm text-brand-text-secondary">
                  Provider
                  <select
                    value={form.chat.provider}
                    onChange={(event) => handleChange('chat', 'provider', event.target.value as LLMProvider)}
                    className="mt-1 w-full px-3 py-2 rounded-md bg-brand-surface-2 border border-brand-surface-2 text-brand-text focus:outline-none focus:ring-2 focus:ring-brand-accent"
                  >
                    {providers.map((provider) => (
                      <option key={provider.value} value={provider.value}>
                        {provider.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-sm text-brand-text-secondary">
                  Temperature
                  <Input
                    type="number"
                    step="0.05"
                    value={form.chat.temperature}
                    onChange={(event) => handleChange('chat', 'temperature', event.target.value)}
                  />
                </label>
                <p className="text-xs text-brand-text-secondary">
                  The copilot uses these settings when summarising state, advising on trades, or executing actions you approve.
                </p>
              </section>
            )}
          </form>
        </div>

        <footer className="px-6 py-4 border-t border-brand-surface-2 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={reset}
              className="px-3 py-1 text-sm text-brand-text-secondary hover:text-brand-text transition"
            >
              Reset to defaults
            </button>
            {statusMessage && <span className="text-xs text-brand-text-secondary">{statusMessage}</span>}
          </div>
          <button
            type="button"
            onClick={saveChanges}
            className="px-4 py-2 bg-brand-accent hover:bg-brand-accent-hover rounded-md text-sm font-semibold"
          >
            Save
          </button>
        </footer>
      </aside>
    </div>
  );
};

