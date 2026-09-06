import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface ThermodynamicsData {
  gas: number;
  liquid: number;
  ice: number;
  snowflakes: number;
  total: number;
  timestamp: string;
}

export const useV2Thermodynamics = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'thermodynamics', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) {
        throw new Error('No environment selected');
      }

      try {
        return await v2ApiClient.get<ThermodynamicsData>(
          `/environments/${currentEnvId}/thermodynamics`
        );
      } catch (error) {
        console.warn('V2 Thermodynamics API failed, returning null', error);
        return null;
      }
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
  });
};
