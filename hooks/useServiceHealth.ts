import { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';
import { ServiceHealthStatus } from '../types/api';

/**
 * Hook to monitor the health status of external services
 * Polls the /health/services endpoint every 30 seconds
 */
export const useServiceHealth = () => {
  const [health, setHealth] = useState<ServiceHealthStatus>({
    alpaca: 'disconnected',
    supabase: 'disconnected',
    openrouter: 'disconnected',
    perplexity: 'disconnected',
  });

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await apiClient.get<ServiceHealthStatus>('/health/services');
        setHealth(data);
      } catch (error) {
        console.error('Failed to fetch service health:', error);
        setHealth({
          alpaca: 'error',
          supabase: 'error',
          openrouter: 'error',
          perplexity: 'error',
        });
      }
    };

    // Fetch immediately on mount
    fetchHealth();

    // Poll every 30 seconds
    const interval = setInterval(fetchHealth, 30000);

    return () => clearInterval(interval);
  }, []);

  return health;
};
