import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';

export const useDashboardMetricsQuery = (filter: {
  startDate: string;
  endDate: string;
  range: string;
}) => {
  return useQuery({
    queryKey: ['dashboardMetrics', filter],
    queryFn: () => api.get('/admin/dashboard/metrics', {
        params: {
          time_range: filter.range,
          start_date: filter.startDate,
          end_date: filter.endDate
        }
      }),
  });
};
