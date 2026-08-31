import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { policyService } from '../../services/policyService';

export const usePolicyQuery = () => {
  return useQuery({
    queryKey: ['policies'],
    queryFn: () => policyService.getPolicies(),
    staleTime: 60000,
  });
};

export const useCreatePolicyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: any) => policyService.createPolicy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] });
    },
  });
};

export const useUpdatePolicyMutation = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => policyService.updatePolicy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] });
    },
  });
};
