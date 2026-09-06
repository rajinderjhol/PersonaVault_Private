import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface Agent {
  id: string;
  name: string;
  type?: string;
  status: 'thinking' | 'active' | 'completed' | 'error' | 'idle';
  lastActivity?: string;
  content?: string;
  timestamp?: string;
}

export const useV2Agents = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'agents', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) {
        throw new Error('No environment selected');
      }

      // In a real implementation, this would call the V2 agents endpoint
      // For now, we'll try the endpoint but handle potential 404/mock if needed
      try {
        return await v2ApiClient.get<Agent[]>(
          `/environments/${currentEnvId}/agents`
        );
      } catch (error) {
        console.warn('V2 Agents API failed, returning empty list', error);
        return [];
      }
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
  });
};
