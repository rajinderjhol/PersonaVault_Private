import { create } from 'zustand';
import { thermodynamicsAPI } from '../api/thermodynamics';
import type { PhaseDistribution, Transition, Snowflake } from '../api/thermodynamics';

interface ThermodynamicsState {
  // State
  phases: PhaseDistribution | null;
  transitions: Transition[];
  snowflakes: Snowflake[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  fetchPhases: () => Promise<void>;
  fetchTransitions: () => Promise<void>;
  fetchSnowflakes: () => Promise<void>;
  freeze: (patternId: string) => Promise<void>;
  melt: (patternId: string) => Promise<void>;
  evaporate: (patternId: string) => Promise<void>;
  sublimate: (patternId: string) => Promise<void>;
  refreshAll: () => Promise<void>;
}

export const useThermodynamicsStore = create<ThermodynamicsState>((set, get) => ({
  // Initial state
  phases: null,
  transitions: [],
  snowflakes: [],
  isLoading: false,
  error: null,
  lastUpdated: null,

  // Fetch phase distribution
  fetchPhases: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await thermodynamicsAPI.getPhaseDistribution();
      set({ phases: data, isLoading: false, lastUpdated: new Date().toISOString() });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Fetch recent transitions
  fetchTransitions: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await thermodynamicsAPI.getTransitions(10);
      set({ transitions: data, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Fetch snowflakes
  fetchSnowflakes: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await thermodynamicsAPI.getSnowflakes();
      set({ snowflakes: data, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Manual phase controls
  freeze: async (patternId: string) => {
    try {
      await thermodynamicsAPI.manualFreeze(patternId);
      await get().refreshAll();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  melt: async (patternId: string) => {
    try {
      await thermodynamicsAPI.manualMelt(patternId);
      await get().refreshAll();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  evaporate: async (patternId: string) => {
    try {
      await thermodynamicsAPI.manualEvaporate(patternId);
      await get().refreshAll();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  sublimate: async (patternId: string) => {
    try {
      await thermodynamicsAPI.manualSublimate(patternId);
      await get().refreshAll();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  // Refresh all thermodynamic data
  refreshAll: async () => {
    await Promise.all([
      get().fetchPhases(),
      get().fetchTransitions(),
      get().fetchSnowflakes(),
    ]);
  },
}));
