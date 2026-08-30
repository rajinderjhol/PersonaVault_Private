import { create } from 'zustand';
import { apiClient } from '../api/client';

interface CrystallizationConfig {
  auto_crystallize: boolean;
  min_confidence: number;
  min_occurrences: number;
  max_age_days: number;
  batch_size: number;
}

interface CrystallizationStats {
  total_patterns: number;
  crystallized: number;
  pending: number;
  rate: number;
  last_run: string | null;
}

interface CrystallizationState {
  config: CrystallizationConfig | null;
  stats: CrystallizationStats | null;
  isLoading: boolean;
  error: string | null;
  fetchConfig: () => Promise<void>;
  fetchStats: () => Promise<void>;
  updateConfig: (key: string, value: any) => Promise<void>;
  triggerCrystallization: () => Promise<void>;
}

export const useCrystallizationStore = create<CrystallizationState>((set, get) => ({
  config: null,
  stats: null,
  isLoading: false,
  error: null,

  fetchConfig: async () => {
    try {
      const response = await apiClient.get('/admin/learning/config');
      set({ config: response.data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchStats: async () => {
    try {
      const response = await apiClient.get('/admin/learning/stats');
      set({ stats: response.data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  updateConfig: async (key: string, value: any) => {
    try {
      await apiClient.post('/admin/learning/config', { [key]: value });
      await get().fetchConfig();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  triggerCrystallization: async () => {
    try {
      await apiClient.post('/admin/learning/crystallization/trigger');
      await get().fetchStats();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },
}));
