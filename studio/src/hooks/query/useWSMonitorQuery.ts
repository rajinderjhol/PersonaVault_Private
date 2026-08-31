import { useQuery } from '@tanstack/react-query';
import { wsMonitorService } from '../../services/wsMonitorService';

export const useWSMonitorQuery = () => {
  return useQuery({
    queryKey: ['ws-monitor'],
    queryFn: async () => {
      const [status, connections] = await Promise.all([
        wsMonitorService.getStatus(),
        wsMonitorService.getConnections(),
      ]);
      return { status, connections };
    },
    staleTime: 5000,
  });
};
