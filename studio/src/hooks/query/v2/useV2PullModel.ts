import { useMutation, useQueryClient } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export const useV2PullModel = () => {
  const queryClient = useQueryClient();
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (name: string) => {
      if (!currentEnvId) throw new Error('No environment selected');
      return await v2ApiClient.post(`/environments/${currentEnvId}/models/pull`, { name });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2', 'models'] });
    }
  });
};
