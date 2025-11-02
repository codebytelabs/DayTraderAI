export type CopilotMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export interface CopilotRequest {
  prompt: string;
  context: string;
  history: CopilotMessage[];
  backendUrl?: string;
}

export interface CopilotResult {
  provider: string;
  content: string;
  route?: {
    category: string;
    targets: string[];
    confidence: number;
    symbols: string[];
    notes: string[];
  };
  confidence?: number;
  citations?: unknown[];
  notes?: string[];
  highlights?: string[];
  contextSummary?: string;
  timestamp?: string;
}

const resolveBackendUrl = (override?: string): string => {
  if (override) {
    return override;
  }

  if (import.meta.env.VITE_BACKEND_URL) {
    return import.meta.env.VITE_BACKEND_URL;
  }

  if (typeof window !== 'undefined') {
    try {
      const storedConfig = window.localStorage.getItem('daytraderai.config.v1');
      if (storedConfig) {
        const parsed = JSON.parse(storedConfig) as { backend?: { apiBaseUrl?: string } };
        if (parsed?.backend?.apiBaseUrl) {
          return parsed.backend.apiBaseUrl;
        }
      }
      const legacy = window.localStorage.getItem('daytraderai.backend_url');
      if (legacy) {
        return legacy;
      }
    } catch (error) {
      console.warn('Failed to resolve backend URL from storage', error);
    }
  }

  return 'http://localhost:8006';
};

export const invokeCopilot = async ({ prompt, context, history, backendUrl }: CopilotRequest): Promise<CopilotResult> => {
  try {
    const API_BASE = resolveBackendUrl(backendUrl);

    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: prompt,
        history: history.map((entry) => ({ role: entry.role, content: entry.content })),
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend chat failed: ${response.status}`);
    }

    const data = await response.json();
    return {
      provider: data.provider || 'DayTraderAI Copilot',
      content: data.content || data.response || 'No response from AI',
      confidence: data.confidence,
      citations: data.citations,
      notes: data.notes,
      highlights: data.highlights,
      contextSummary: data.context_summary,
      route: data.route,
      timestamp: data.timestamp,
    };
  } catch (error) {
    console.error('Backend chat request failed, falling back to local summary', error);
    return fallbackSummary(prompt, context, 'Backend connection error');
  }
};

const fallbackSummary = (prompt: string, context: string, reason: string): CopilotResult => {
  const lines = [
    `Fallback copilot active (${reason}).`,
    'Current conditions:',
    ...context.split('\n').slice(0, 6).map((line) => `- ${line.trim()}`),
    '',
    `Request: ${prompt}`,
    'Suggested next step: verify Alpaca connectivity, review latest logs, and rerun the desired action manually.',
  ];
  return {
    provider: 'Local summary',
    content: lines.join('\n'),
    route: {
      category: 'fallback',
      targets: ['local'],
      confidence: 0.2,
      symbols: [],
      notes: [reason],
    },
    confidence: 0.2,
    notes: [reason],
    highlights: [],
    contextSummary: context,
  };
};
