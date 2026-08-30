import { apiClient } from './client';

export interface Trace {
  id: string;
  session_id: number;
  step: string;
  timestamp: string;
  data: Record<string, any>;
  confidence_score: number;
  is_crystallized: boolean;
  agent_id?: string;
  query?: string;
  response?: string;
}

export interface TraceDetail extends Trace {
  provenance_links: Array<{
    id: string;
    source_type: string;
    source_id: string;
    source_text: string;
    relevance_score: number;
  }>;
}

export const tracesAPI = {
  // Get recent traces for the feed
  getRecent: async (limit: number = 10): Promise<Trace[]> => {
    const response = await apiClient.get(`/traces/recent?limit=${limit}`);
    return response.data;
  },

  // Get traces for a specific session
  getSessionTraces: async (sessionId: number): Promise<Trace[]> => {
    const response = await apiClient.get(`/traces/session/${sessionId}`);
    return response.data;
  },

  // Get a single trace with full details
  getTrace: async (traceId: string): Promise<TraceDetail> => {
    const response = await apiClient.get(`/traces/${traceId}`);
    return response.data;
  },

  // Crystallize a trace
  crystallize: async (traceId: string): Promise<{ status: string; trace_id: string }> => {
    const response = await apiClient.post(`/traces/${traceId}/crystallize`);
    return response.data;
  },
};
