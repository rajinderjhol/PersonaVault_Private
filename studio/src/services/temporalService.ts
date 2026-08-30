import { api } from './api';

export interface SearchParams {
  query: string;
  time_range?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  confidence_score: number;
  temporal_relevance?: {
    score: number;
    context: string;
    factors: string[];
  };
  created_at: string;
  domain: string;
}

export interface SearchResponse {
  items: SearchResult[];
  total: number;
  temporal_metadata: {
    context: any;
    scoring_enabled: boolean;
    relevance_threshold: number;
  };
}

export const temporalService = {
  // Existing metrics method
  getMetrics: (params: { time_range?: string; start_date?: string; end_date?: string }) =>
    api.get('/api/v1/dashboard/metrics', { params }),
  
  // Enhanced search method with temporal filtering
  search: async (params: SearchParams): Promise<SearchResponse> => {
    const response = await api.get('/api/v1/search', { 
      params: {
        query: params.query,
        time_range: params.time_range,
        start_date: params.start_date,
        end_date: params.end_date,
        limit: params.limit || 20,
        offset: params.offset || 0
      }
    });
    return response.data;
  },
  
  // Method to get temporal insights for the widget
  getTemporalInsights: (params?: { time_range?: string }) =>
    api.get('/api/v1/temporal/metrics', { params })
};
