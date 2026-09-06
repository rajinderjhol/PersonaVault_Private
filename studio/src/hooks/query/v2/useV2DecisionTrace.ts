import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface DecisionStep {
  label: string;
  details: string;
  timestamp: string;
  status: 'completed' | 'processing' | 'pending';
}

export interface DecisionTrace {
  id: string;
  summary: string;
  verdict: string;
  steps: DecisionStep[];
}

export const useV2DecisionTrace = (decisionId: string) => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'decision', 'trace', currentEnvId, decisionId],
    queryFn: async () => {
      if (!currentEnvId || !decisionId) {
        throw new Error('Missing environment or decision ID');
      }

      try {
        return await v2ApiClient.get<DecisionTrace>(
          `/environments/${currentEnvId}/decisions/${decisionId}/trace`
        );
      } catch (error) {
        console.warn('V2 Decision Trace API failed', error);
        return null;
      }
    },
    enabled: !!currentEnvId && !!decisionId,
    staleTime: 60000,
  });
};
