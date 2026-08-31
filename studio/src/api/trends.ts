import { apiClient } from './client';

export interface TrendData {
  label: string;
  value: number;
  timestamp: string;
}

export interface DomainTrend {
  name: string;
  values: number[];
  labels: string[];
}

export const trendsAPI = {
  getTrends: async (domain: string = 'confidence', days: number = 30): Promise<DomainTrend[]> => {
    return await apiClient.get(`/timeline/trends/${domain}?days=${days}`);
  },
};
