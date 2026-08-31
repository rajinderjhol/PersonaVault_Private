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
    return await apiClient.get('/thermodynamics/phase-distribution');
  },

  // Get recent transitions
  getTransitions: async (limit: number = 10): Promise<Transition[]> => {
    return await apiClient.get(`/thermodynamics/transitions?limit=${limit}`);
  },

  // List snowflakes
  getSnowflakes: async (): Promise<Snowflake[]> => {
    return await apiClient.get('/thermodynamics/snowflakes');
  },

  // Manual phase controls
  manualFreeze: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    return await apiClient.post('/thermodynamics/manual/freeze', { pattern_id: patternId });
  },

  manualMelt: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    return await apiClient.post('/thermodynamics/manual/melt', { pattern_id: patternId });
  },

  manualEvaporate: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    return await apiClient.post('/thermodynamics/manual/evaporate', { pattern_id: patternId });
  },

  manualSublimate: async (patternId: string): Promise<{ status: string; message: string; new_phase: string }> => {
    return await apiClient.post('/thermodynamics/manual/sublimate', { pattern_id: patternId });
  },
};
