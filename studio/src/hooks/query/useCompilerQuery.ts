import { useQuery } from '@tanstack/react-query';
import { compilerService } from '../../services/compilerService';

export const useCompilerQuery = () => {
  return useQuery({
    queryKey: ['compiler-packs'],
    queryFn: () => compilerService.getPacks(),
    staleTime: 60000,
  });
};
