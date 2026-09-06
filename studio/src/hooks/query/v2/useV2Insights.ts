import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface IntelligenceInsight {
  id: string;
  type: 'security' | 'optimization' | 'agent' | 'learning';
  message: string;
  actionLabel?: string;
  actionType?: string;
  priority: 'low' | 'medium' | 'high';
  timestamp: string;
}

export const useV2Insights = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'insights', currentEnvId],
    queryFn: async () => {
      // Mock insights for now, to be replaced with real backend logic
      const insights: IntelligenceInsight[] = [
        {
          id: 'ins-001',
          type: 'security',
          message: 'Security Agent has processed 47 decisions this week. 12 require policy refinement.',
          actionLabel: 'Review Top 5',
          priority: 'high',
          timestamp: new Date().toISOString()
        },
        {
          id: 'ins-002',
          type: 'optimization',
          message: 'Memory compression efficiency reached 99.7%. 5 new patterns crystallized.',
          actionLabel: 'View Patterns',
          priority: 'medium',
          timestamp: new Date().toISOString()
        },
        {
          id: 'ins-003',
          type: 'agent',
          message: 'Reasoning swarm load is increasing. Consider scaling environment resources.',
          actionLabel: 'Scale Swarm',
          priority: 'medium',
          timestamp: new Date().toISOString()
        }
      ];

      return insights;
    },
    enabled: !!currentEnvId,
    staleTime: 60000,
  });
};
