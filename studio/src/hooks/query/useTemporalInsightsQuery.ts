import { useQuery } from '@tanstack/react-query';
import { temporalService } from '../../services/temporalService';

export const useTemporalInsightsQuery = (timeRange: string) => {
  return useQuery({
    queryKey: ['temporalInsights', timeRange],
    queryFn: () => temporalService.getTemporalInsights({ time_range: timeRange }),
  });
};
