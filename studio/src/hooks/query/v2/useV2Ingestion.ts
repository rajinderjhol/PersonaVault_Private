import { useMutation, useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export const useV2StartIngestion = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (folderPath: string) => {
      if (!currentEnvId) throw new Error('No environment selected');
      return await v2ApiClient.post(`/environments/${currentEnvId}/ingestion/folder`, { folder_path: folderPath });
    }
  });
};

export const useV2IngestionStatus = (jobId: string | null) => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'ingestion', jobId],
    queryFn: async () => {
      if (!currentEnvId || !jobId) throw new Error('No environment or job ID');
      return await v2ApiClient.get(`/environments/${currentEnvId}/ingestion/job/${jobId}`);
    },
    enabled: !!currentEnvId && !!jobId,
    refetchInterval: (query) => (query.state.data?.status === 'completed' ? false : 2000),
  });
};

export const useV2Documents = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'documents', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return await v2ApiClient.get(`/environments/${currentEnvId}/documents`);
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
  });
};
