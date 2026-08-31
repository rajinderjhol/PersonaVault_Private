import { useQuery } from '@tanstack/react-query';
import { verilinkService } from '../../services/verilinkService';

export const useVerilinkQuery = () => {
  return useQuery({
    queryKey: ['verilink-status'],
    queryFn: () => verilinkService.getStatus(),
    staleTime: 60000,
  });
};
