import { useMutation, useQueryClient } from '@tanstack/react-query';
import { marketplaceService } from '../../services/marketplaceService';

export const useInstallPackMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: string) => marketplaceService.installItem(itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['marketplace'] });
    },
  });
};
