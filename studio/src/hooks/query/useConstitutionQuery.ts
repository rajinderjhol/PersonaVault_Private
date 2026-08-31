import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { constitutionService } from '../../services/constitutionService';

export const useConstitutionQuery = () => {
  return useQuery({
    queryKey: ['constitution'],
    queryFn: () => constitutionService.getConstitution(),
    staleTime: 60000,
  });
};

export const useUpdateConstitutionMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => constitutionService.updateConstitution(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['constitution'] });
    },
  });
};
