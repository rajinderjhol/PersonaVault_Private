import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

interface DashboardMetrics {
  total_memories: number;
  total_memories_trend?: 'up' | 'down' | 'stable';
  active_sessions: number;
  active_sessions_trend?: 'up' | 'down' | 'stable';
  crystallization_rate: number;
  storage_used: number;
  temporal: {
    velocity: number;
    decay_rate: number;
    aging_patterns: number;
  };
  provider: string;
  mode: string;
  latency: number;
  confidence: number;
}

export const useV2DashboardMetrics = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'dashboard', 'metrics', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) {
        throw new Error('No environment selected');
      }

      return await v2ApiClient.get<DashboardMetrics>(
        `/environments/${currentEnvId}/metrics`
      );
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
    refetchInterval: 60000,
  });
};
