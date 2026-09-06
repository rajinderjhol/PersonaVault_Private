import { useMutation } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface SearchParams {
  query: string;
  limit?: number;
}

export interface SearchResult {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
}

export const useV2Search = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (params: SearchParams) => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.post<SearchResult[]>(
        `/environments/${currentEnvId}/search`,
        params
      );
    },
  });
};
