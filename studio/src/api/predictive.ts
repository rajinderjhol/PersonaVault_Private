import { apiClient } from './client';

export interface DriftData {
  overall: number;
  security: number;
  compliance: number;
  contract: number;
  procurement: number;
}

export interface RiskData {
  high: number;
  medium: number;
  low: number;
}

export interface Insight {
  id: string;
  type: string;
  title: string;
  description: string;
  confidence: number;
  timestamp: string;
}

export interface Suggestion {
  id: string;
  title: string;
  description: string;
  action: string;
  confidence: number;
}

export const predictiveAPI = {
  getDrift: async (): Promise<DriftData> => {
    return await apiClient.get('/predictive/drift');
  },

  getRisks: async (): Promise<RiskData> => {
    return await apiClient.get('/predictive/risks');
  },

  getInsights: async (): Promise<Insight[]> => {
    return await apiClient.get('/predictive/insights');
  },

  getSuggestions: async (): Promise<Suggestion[]> => {
    return await apiClient.get('/predictive/suggestions');
  },

  dismissSuggestion: async (suggestionId: string): Promise<void> => {
    await apiClient.post(`/predictive/suggestions/${suggestionId}/dismiss`);
  },

  executeSuggestion: async (suggestionId: string): Promise<any> => {
    return await apiClient.post(`/predictive/suggestions/${suggestionId}/execute`);
  },
};
