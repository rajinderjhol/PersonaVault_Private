import { useQuery } from '@tanstack/react-query';
import { marketplaceService } from '../../services/marketplaceService';

export const useMarketplaceQuery = () => {
  return useQuery({
    queryKey: ['marketplace'],
    queryFn: () => marketplaceService.getMarketplaceItems(),
    staleTime: 60000,
  });
};
