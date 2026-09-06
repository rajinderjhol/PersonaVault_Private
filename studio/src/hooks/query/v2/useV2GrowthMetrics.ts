import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface GrowthMetricPoint {
  date: string;
  count: number;
  type: 'memory' | 'crystallized' | 'compression';
}

export interface GrowthMetrics {
  totalMemories: number;
  crystallizedCount: number;
  compressionRatio: number;
  memoryHistory: GrowthMetricPoint[];
  compressionHistory: { date: string; ratio: number }[];
}

export const useV2GrowthMetrics = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'intelligence', 'growth', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) {
        throw new Error('No environment selected');
      }

      try {
        return await v2ApiClient.get<GrowthMetrics>(
          `/environments/${currentEnvId}/intelligence/growth`
        );
      } catch (error) {
        console.warn('V2 Growth Metrics API failed', error);
        return null;
      }
    },
    enabled: !!currentEnvId,
    staleTime: 300000, // 5 minutes
  });
};
