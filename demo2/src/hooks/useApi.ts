import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

// Generic hook for API calls with loading and error states
export function useApi<T>(
  apiCall: () => Promise<T>,
  dependencies: any[] = [],
  immediate: boolean = true
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(immediate);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiCall();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { data, loading, error, refetch: execute };
}

// Specific hooks for different API endpoints
export function useDashboardMetrics() {
  return useApi(() => apiService.getDashboardMetrics(), [], true);
}

export function useRecentCalls(limit: number = 10) {
  return useApi(() => apiService.getRecentCalls(limit), [limit], true);
}

export function useSystemStatus() {
  return useApi(() => apiService.getSystemStatus(), [], true);
}

export function useCalls(page: number = 1, perPage: number = 50, status?: string) {
  return useApi(
    () => apiService.getCalls(page, perPage, status),
    [page, perPage, status],
    true
  );
}

export function useCallDetails(callId: number) {
  return useApi(
    () => apiService.getCallDetails(callId),
    [callId],
    true
  );
}

export function useAppointments(page: number = 1, perPage: number = 50) {
  return useApi(
    () => apiService.getAppointments(page, perPage),
    [page, perPage],
    true
  );
}

// Custom hook for real-time updates (polling)
export function useRealTimeUpdates<T>(
  apiCall: () => Promise<T>,
  interval: number = 30000, // 30 seconds
  enabled: boolean = true
) {
  const { data, loading, error, refetch } = useApi(apiCall, [], true);

  useEffect(() => {
    if (!enabled) return;

    const intervalId = setInterval(() => {
      refetch();
    }, interval);

    return () => clearInterval(intervalId);
  }, [refetch, interval, enabled]);

  return { data, loading, error, refetch };
}