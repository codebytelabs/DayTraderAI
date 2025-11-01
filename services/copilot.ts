import { AppConfig } from '../state/ConfigContext';

export type CopilotMessage = {
  role: 'system' | 'user' | 'assistant';
  content: string;
};

export interface CopilotRequest {
  prompt: string;
  context: string;
  history: CopilotMessage[];
  config: AppConfig;
}

export interface CopilotResult {
  provider: string;
  content: string;
}

const OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions';
const PERPLEXITY_URL = 'https://api.perplexity.ai/chat/completions';

const SYSTEM_PROMPT = `You are the DayTraderAI copilot. You understand every subsystem: Alpaca execution, Supabase analytics, Perplexity news, OpenRouter LLM guidance, and deterministic risk rails.

Always:
- Explain reasoning in bullet-point style paragraphs.
- Surface risks, blockers, or missing configuration.
- Suggest next steps for novice traders.
- Prefer actionable, concise language.
- If you cannot execute an action, clearly say so and suggest how the user can proceed.

When summarising the trading state, highlight: equity trend, win rate, open positions, pending orders, and notable log messages.`;

export const invokeCopilot = async ({ prompt, context, history, config }: CopilotRequest): Promise<CopilotResult> => {
  const provider = config.chat.provider;

  if (provider === 'openrouter' && config.openRouter.apiKey) {
    try {
      const response = await fetch(OPENROUTER_URL, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${config.openRouter.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: config.openRouter.model,
          temperature: config.chat.temperature,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            ...history.slice(-4),
            { role: 'user', content: `${prompt}\n\n<current_state>\n${context}\n</current_state>` },
          ],
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text);
      }
      const data = await response.json();
      const content = data?.choices?.[0]?.message?.content ?? 'No response from OpenRouter.';
      return { provider: `OpenRouter (${config.openRouter.model})`, content };
    } catch (error) {
      console.error('OpenRouter request failed, falling back to local summary', error);
      return fallbackSummary(prompt, context, 'OpenRouter error');
    }
  }

  if (provider === 'perplexity' && config.perplexity.apiKey) {
    try {
      const response = await fetch(PERPLEXITY_URL, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${config.perplexity.apiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: config.perplexity.model,
          temperature: config.chat.temperature,
          messages: [
            { role: 'system', content: SYSTEM_PROMPT },
            ...history.slice(-4),
            { role: 'user', content: `${prompt}\n\n<current_state>\n${context}\n</current_state>` },
          ],
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text);
      }
      const data = await response.json();
      const content = data?.choices?.[0]?.message?.content ?? 'No response from Perplexity.';
      return { provider: `Perplexity (${config.perplexity.model})`, content };
    } catch (error) {
      console.error('Perplexity request failed, falling back to local summary', error);
      return fallbackSummary(prompt, context, 'Perplexity error');
    }
  }

  return fallbackSummary(prompt, context, provider === 'none' ? 'LLM disabled' : 'Missing API key');
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
  };
};

