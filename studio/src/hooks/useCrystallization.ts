import { useEffect } from 'react';
import { useCrystallizationStore } from '../store/crystallizationStore';

export const useCrystallization = (autoFetch: boolean = true) => {
  const {
    config,
    stats,
    isLoading,
    error,
    fetchConfig,
    fetchStats,
    updateConfig,
    triggerCrystallization,
  } = useCrystallizationStore();

  useEffect(() => {
    if (autoFetch) {
      fetchConfig();
      fetchStats();
    }
  }, [autoFetch]);

  return {
    config,
    stats,
    isLoading,
    error,
    updateConfig,
    triggerCrystallization,
  };
};
