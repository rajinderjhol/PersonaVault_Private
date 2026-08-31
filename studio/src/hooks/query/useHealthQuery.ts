import { useQuery } from '@tanstack/react-query';
import { healthService } from '../../services/healthService';

export const useHealthQuery = () => {
  return useQuery({
    queryKey: ['system-health'],
    queryFn: async () => {
      const [health, metrics] = await Promise.all([
        healthService.getHealth(),
        healthService.getMetrics(),
      ]);
      return { health, metrics };
    },
    staleTime: 30000,
  });
};
