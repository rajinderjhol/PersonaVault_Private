import { useQuery } from '@tanstack/react-query';
import { ingestionApi } from '../../services/ingestionService';

export const useJobStatusQuery = (jobId: string | null) => {
  return useQuery({
    queryKey: ['jobStatus', jobId],
    queryFn: async () => {
      if (!jobId) return null;
      const response = await ingestionApi.getJobStatus(jobId);
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: (query) => {
        const status = query.state.data?.status;
        return status === 'completed' || status === 'failed' ? false : 2000;
    },
  });
};
