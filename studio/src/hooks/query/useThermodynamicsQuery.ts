import { useQuery } from '@tanstack/react-query';
import { thermodynamicsAPI } from '../../api/thermodynamics';

export const useThermodynamicsQuery = () => {
  return useQuery({
    queryKey: ['thermodynamics'],
    queryFn: async () => {
      const [phases, transitions, snowflakes] = await Promise.all([
        thermodynamicsAPI.getPhaseDistribution(),
        thermodynamicsAPI.getTransitions(),
        thermodynamicsAPI.getSnowflakes(),
      ]);
      return { phases, transitions, snowflakes };
    },
  });
};
