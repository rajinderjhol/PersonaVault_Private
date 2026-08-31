import { useQuery } from '@tanstack/react-query';
import { memoryService } from '../../services/memoryService';

export const useMemoryQuery = () => {
  return useQuery({
    queryKey: ['memory-lattice'],
    queryFn: () => memoryService.getLattice(),
    staleTime: 60000,
  });
};
