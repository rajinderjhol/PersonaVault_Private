import { apiClient } from './client';

export interface ModeConfig {
  mode: 'standard' | 'restricted' | 'simulation' | 'audit';
  config: {
    tools_enabled: boolean;
    hitl_required: boolean;
    ice_memory_only: boolean;
    sandboxed: boolean;
    logging_level: string;
  };
}

export const modeAPI = {
  getCurrentMode: async (): Promise<ModeConfig> => {
    return await apiClient.get('/mode/current');
  },

  setMode: async (mode: string): Promise<void> => {
    await apiClient.post(`/mode/set?mode=${mode.toLowerCase()}`);
  },
};
