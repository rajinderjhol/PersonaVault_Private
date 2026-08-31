import { useEffect } from 'react';
import { useThermodynamicsStore } from '../store/thermodynamicsStore';

export const useThermodynamics = (autoRefresh: boolean = true, interval: number = 60000) => {
  const {
    phases,
    transitions,
    snowflakes,
    isLoading,
    error,
    lastUpdated,
    fetchPhases,
    fetchTransitions,
    fetchSnowflakes,
    refreshAll,
    freeze,
    melt,
    evaporate,
    sublimate,
  } = useThermodynamicsStore();

  // Auto-refresh on mount and at interval
  useEffect(() => {
    if (autoRefresh) {
      // Small delay to allow auth to stabilize before fetching
      const initialDelay = setTimeout(() => {
        refreshAll();
      }, 2000);
      
      const timer = setInterval(refreshAll, interval);
      
      return () => {
        clearTimeout(initialDelay);
        clearInterval(timer);
      };
    }
  }, [autoRefresh, interval]);

  return {
    // Data
    phases,
    transitions,
    snowflakes,
    isLoading,
    error,
    lastUpdated,

    // Actions
    fetchPhases,
    fetchTransitions,
    fetchSnowflakes,
    refreshAll,

    // Manual controls
    freeze,
    melt,
    evaporate,
    sublimate,
  };
};
