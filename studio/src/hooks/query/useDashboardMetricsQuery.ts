import { useQuery } from '@tanstack/react-query';
import { api } from '../../services/api';
import { useAuthStore } from '../../store/authStore';

export const useDashboardMetricsQuery = (filter: {
  startDate: string;
  endDate: string;
  range: string;
}) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  return useQuery({
    queryKey: ['dashboardMetrics', filter],
    queryFn: () => api.get('/admin/dashboard/metrics', {
        params: {
          time_range: filter.range,
          start_date: filter.startDate,
          end_date: filter.endDate
        }
      }),
    enabled: isAuthenticated,
  });
};
