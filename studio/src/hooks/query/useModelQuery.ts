import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelService } from '../../services/modelService';

export const useModelQuery = () => {
  const queryClient = useQueryClient();

  const modelsQuery = useQuery({
    queryKey: ['models'],
    queryFn: () => modelService.getModels(),
    staleTime: 60000,
  });

  const addModelMutation = useMutation({
    mutationFn: modelService.addModel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  });

  const updateModelMutation = useMutation({
    mutationFn: ({ modelId, modelData }: { modelId: string; modelData: any }) =>
      modelService.updateModel(modelId, modelData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  });

  const deleteModelMutation = useMutation({
    mutationFn: modelService.deleteModel,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['models'] }),
  });

  return { modelsQuery, addModelMutation, updateModelMutation, deleteModelMutation };
};
