import { useQuery } from '@tanstack/react-query';
import { securityService } from '../../services/securityService';

export const useSecurityQuery = () => {
  return useQuery({
    queryKey: ['security'],
    queryFn: async () => {
      const [events, intelligence] = await Promise.all([
        securityService.getSecurityEvents(),
        securityService.getSecurityIntelligence(),
      ]);
      return { events, intelligence };
    },
    staleTime: 30000,
  });
};
