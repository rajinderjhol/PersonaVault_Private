import { useMutation, useQueryClient } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export const useV2DeleteModel = () => {
  const queryClient = useQueryClient();
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (modelName: string) => {
      if (!currentEnvId) throw new Error('No environment selected');
      // The router expects /{model_name}
      return await v2ApiClient.delete(`/environments/${currentEnvId}/models/${modelName}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['v2', 'models'] });
    }
  });
};
