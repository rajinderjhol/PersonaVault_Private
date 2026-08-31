import { useQuery } from '@tanstack/react-query';
import { governanceService } from '../../services/governanceService';

export const useGovernanceQuery = () => {
  return useQuery({
    queryKey: ['governance-overview'],
    queryFn: () => governanceService.getOverview(),
    staleTime: 60000,
  });
};
