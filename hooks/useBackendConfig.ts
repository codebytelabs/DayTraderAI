import { useState, useEffect } from 'react';
import { apiClient } from '../lib/apiClient';
import { BackendConfig } from '../types/api';

/**
 * Hook to load configuration defaults from the backend
 * Fetches from /config endpoint on mount
 */
export const useBackendConfig = () => {
  const [config, setConfig] = useState<BackendConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const data = await apiClient.get<BackendConfig>('/config');
      setConfig(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch backend config:', err);
      setError(err instanceof Error ? err.message : 'Failed to load config');
      setConfig(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  return { config, loading, error, refetch: fetchConfig };
};
