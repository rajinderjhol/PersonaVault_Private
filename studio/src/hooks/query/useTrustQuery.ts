import { useQuery } from '@tanstack/react-query';
import { trustService } from '../../services/trustService';

export const useTrustQuery = () => {
  return useQuery({
    queryKey: ['trust-data'],
    queryFn: async () => {
      const [devices, syncStatus] = await Promise.all([
        trustService.getDevices(),
        trustService.getSyncStatus(),
      ]);
      return { devices, syncStatus };
    },
    staleTime: 60000,
  });
};
