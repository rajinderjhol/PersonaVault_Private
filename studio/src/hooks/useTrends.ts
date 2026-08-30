import { useEffect } from 'react';
import { useTrendStore } from '../store/trendStore';

export const useTrends = (autoFetch: boolean = true) => {
  const { trends, domains, isLoading, error, fetchTrends } = useTrendStore();

  useEffect(() => {
    if (autoFetch) {
      fetchTrends();
    }
  }, [autoFetch]);

  return {
    trends,
    domains,
    isLoading,
    error,
    fetchTrends,
  };
};
