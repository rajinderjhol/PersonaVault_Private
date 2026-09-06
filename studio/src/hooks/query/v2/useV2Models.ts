import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface Model {
  id: string;
  name: string;
  provider: string;
  size: string;
  confidence: number;
  latency: number;
  isActive: boolean;
  usedIn: string[];
  status: 'active' | 'available' | 'downloading' | 'error';
}

export const useV2Models = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'models', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      
      // Use the newly implemented V2 endpoint
      const data = await v2ApiClient.get<{models: any[], active_model: string}>(`/environments/${currentEnvId}/models`);
      
      return data.models.map((model: any) => ({
        id: model.name || model.id,
        name: model.name || 'Unknown Model',
        provider: 'Ollama', // Hardcoded as the V1 logic is Ollama-focused
        size: model.size || 'N/A',
        confidence: 92, // Defaulting if not in V1 response
        latency: 50, // Defaulting if not in V1 response
        isActive: model.name === data.active_model,
        usedIn: ['General'],
        status: (model.name === data.active_model ? 'active' : 'available') as 'active' | 'available' | 'downloading' | 'error',
      }));
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
    retry: 2,
  });
};

export const useV2ModelMetrics = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'models', 'metrics', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      // Define the metrics return type
      return await v2ApiClient.get<{
        totalDecisions: number;
        hitRate: string;
        throughput: number;
        confidenceTrend: { label: string, value: number }[];
        latencyTrend: { label: string, value: number }[];
      }>(`/environments/${currentEnvId}/models/metrics`);
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
    retry: 2,
  });
};

export const useV2Providers = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'providers', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      // V2 endpoint exists, let's use it
      return await v2ApiClient.get(`/environments/${currentEnvId}/models/providers`);
    },
    enabled: !!currentEnvId,
    staleTime: 60000,
    retry: 2,
  });
};
