import { useQuery } from '@tanstack/react-query';
import { crystallizationService } from '../../services/crystallizationService';

export const useCrystallizationQuery = () => {
  return useQuery({
    queryKey: ['crystallization-metrics'],
    queryFn: () => crystallizationService.getMetrics(),
    staleTime: 60000,
  });
};
