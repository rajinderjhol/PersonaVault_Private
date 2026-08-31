import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { userService } from '../../services/userService';

export const useUserQuery = () => {
  return useQuery({
    queryKey: ['user-profile'],
    queryFn: () => userService.getProfile(),
    staleTime: 60000,
  });
};

export const useUpdateUserMutation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: any) => userService.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user-profile'] });
    },
  });
};
