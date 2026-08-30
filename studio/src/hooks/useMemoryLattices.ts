import { useEffect } from 'react';
import { useLatticeStore } from '../store/latticeStore';

export const useMemoryLattices = (autoFetch: boolean = true) => {
  const { nodes, edges, isLoading, error, fetchLattices } = useLatticeStore();

  useEffect(() => {
    if (autoFetch) {
      fetchLattices();
    }
  }, [autoFetch]);

  return {
    nodes,
    edges,
    isLoading,
    error,
    fetchLattices,
  };
};
