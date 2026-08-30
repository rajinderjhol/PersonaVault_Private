import { useEffect } from 'react';
import { useTracesStore } from '../store/tracesStore';

export const useTraces = (autoRefresh: boolean = true, interval: number = 30000) => {
  const {
    recentTraces,
    sessionTraces,
    currentTrace,
    isLoading,
    error,
    lastUpdated,
    fetchRecent,
    fetchSessionTraces,
    fetchTrace,
    crystallize,
    clearCurrentTrace,
    refreshAll,
  } = useTracesStore();

  // Auto-refresh on mount and at interval
  useEffect(() => {
    if (autoRefresh) {
      refreshAll();
      const timer = setInterval(refreshAll, interval);
      return () => clearInterval(timer);
    }
  }, [autoRefresh, interval]);

  return {
    // Data
    recentTraces,
    sessionTraces,
    currentTrace,
    isLoading,
    error,
    lastUpdated,

    // Actions
    fetchRecent,
    fetchSessionTraces,
    fetchTrace,
    crystallize,
    clearCurrentTrace,
    refreshAll,
  };
};
