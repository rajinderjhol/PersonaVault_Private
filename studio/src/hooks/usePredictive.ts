import { useEffect } from 'react';
import { usePredictiveStore } from '../store/predictiveStore';

export const usePredictive = (autoFetch: boolean = true) => {
  const {
    drift,
    risks,
    insights,
    suggestions,
    isLoading,
    error,
    fetchAll,
    fetchDrift,
    fetchRisks,
    fetchInsights,
    fetchSuggestions,
    dismissSuggestion,
    executeSuggestion,
  } = usePredictiveStore();

  useEffect(() => {
    if (autoFetch) {
      fetchAll();
    }
  }, [autoFetch]);

  return {
    drift,
    risks,
    insights,
    suggestions,
    isLoading,
    error,
    fetchAll,
    fetchDrift,
    fetchRisks,
    fetchInsights,
    fetchSuggestions,
    dismissSuggestion,
    executeSuggestion,
  };
};
