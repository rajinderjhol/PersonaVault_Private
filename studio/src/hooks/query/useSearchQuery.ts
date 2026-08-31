import { useQuery } from '@tanstack/react-query';
import { temporalService } from '../../services/temporalService';

export const useSearchQuery = (params: {
  query: string;
  timeRange: string;
  startDate: string;
  endDate: string;
}) => {
  return useQuery({
    queryKey: ['search', params],
    queryFn: () => temporalService.search({
        query: params.query,
        time_range: params.timeRange,
        start_date: params.startDate,
        end_date: params.endDate
    }),
    enabled: !!params.query.trim(), // Only fetch if query is not empty
  });
};
