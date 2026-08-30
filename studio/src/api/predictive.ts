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
    const response = await apiClient.get('/predictive/drift');
    return response.data;
  },

  getRisks: async (): Promise<RiskData> => {
    const response = await apiClient.get('/predictive/risks');
    return response.data;
  },

  getInsights: async (): Promise<Insight[]> => {
    const response = await apiClient.get('/predictive/insights');
    return response.data;
  },

  getSuggestions: async (): Promise<Suggestion[]> => {
    const response = await apiClient.get('/predictive/suggestions');
    return response.data;
  },

  dismissSuggestion: async (suggestionId: string): Promise<void> => {
    await apiClient.post(`/predictive/suggestions/${suggestionId}/dismiss`);
  },

  executeSuggestion: async (suggestionId: string): Promise<any> => {
    const response = await apiClient.post(`/predictive/suggestions/${suggestionId}/execute`);
    return response.data;
  },
};
