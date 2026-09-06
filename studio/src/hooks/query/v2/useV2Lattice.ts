import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface MemoryPhase {
  name: string;
  count: number;
  percentage: number;
  color: string;
  description: string;
}

export interface LatticeData {
  phases: MemoryPhase[];
  total: number;
  transitions: {
    from: string;
    to: string;
    count: number;
    timestamp: string;
  }[];
  growth: {
    date: string;
    value: number;
  }[];
  crystallizationRate: number;
  compressionRatio: number;
}

export const useV2Lattice = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'lattice', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<LatticeData>(`/environments/${currentEnvId}/lattice`);
    },
    enabled: !!currentEnvId,
    staleTime: 10000,
    refetchInterval: 15000, // Poll every 15 seconds
  });
};

export const useV2LatticeHistory = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'lattice', 'history', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<LatticeData[]>(`/environments/${currentEnvId}/lattice/history`);
    },
    enabled: !!currentEnvId,
    staleTime: 60000,
  });
};
