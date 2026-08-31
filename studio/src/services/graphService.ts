import { apiClient } from '../api/client';

export const graphService = {
  getDecisionGraph: (decisionId: string) =>
    apiClient.get(`/graph/decision/${decisionId}`),
};
