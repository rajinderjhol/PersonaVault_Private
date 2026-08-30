import { apiClient } from './client';

export interface PhaseDistribution {
  gas: number;
  liquid: number;
  ice: number;
  snowflakes: number;
  total: number;
  timestamp: string;
}

export interface Transition {
  type: string;
  description: string;
  timestamp: string;
}

export interface Snowflake {
  id: string;
  domain: string;
  name: string;
  pattern_count: number;
  confidence: number;
  focus: string[];
}

export const thermodynamicsAPI = {
  // Get current phase distribution
  getPhaseDistribution: async (): Promise<PhaseDistribution> => {
    const response = await apiClient.get('/thermodynamics/phase-distribution');
    return response.data;
  },

  // Get recent transitions
  getTransitions: async (limit: number = 10): Promise<Transition[]> => {
    const response = await apiClient.get(`/thermodynamics/transitions?limit=${limit}`);
    return response.data;
  },

  // List snowflakes
  getSnowflakes: async (): Promise<Snowflake[]> => {
    const response = await apiClient.get('/thermodynamics/snowflakes');
    return response.data;
  },

  // Manual phase controls
  manualFreeze: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    const response = await apiClient.post('/thermodynamics/manual/freeze', { pattern_id: patternId });
    return response.data;
  },

  manualMelt: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    const response = await apiClient.post('/thermodynamics/manual/melt', { pattern_id: patternId });
    return response.data;
  },

  manualEvaporate: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    const response = await apiClient.post('/thermodynamics/manual/evaporate', { pattern_id: patternId });
    return response.data;
  },

  manualSublimate: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    const response = await apiClient.post('/thermodynamics/manual/sublimate', { pattern_id: patternId });
    return response.data;
  },
};
