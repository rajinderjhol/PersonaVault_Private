import { create } from 'zustand';
import { predictiveAPI, DriftData, RiskData, Insight, Suggestion } from '../api/predictive';

interface PredictiveState {
  drift: DriftData | null;
  risks: RiskData | null;
  insights: Insight[];
  suggestions: Suggestion[];
  isLoading: boolean;
  error: string | null;
  fetchAll: () => Promise<void>;
  fetchDrift: () => Promise<void>;
  fetchRisks: () => Promise<void>;
  fetchInsights: () => Promise<void>;
  fetchSuggestions: () => Promise<void>;
  dismissSuggestion: (id: string) => Promise<void>;
  executeSuggestion: (id: string) => Promise<void>;
}

export const usePredictiveStore = create<PredictiveState>((set, get) => ({
  drift: null,
  risks: null,
  insights: [],
  suggestions: [],
  isLoading: false,
  error: null,

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    try {
      await Promise.all([
        get().fetchDrift(),
        get().fetchRisks(),
        get().fetchInsights(),
        get().fetchSuggestions(),
      ]);
    } catch (error) {
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },

  fetchDrift: async () => {
    try {
      const data = await predictiveAPI.getDrift();
      set({ drift: data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchRisks: async () => {
    try {
      const data = await predictiveAPI.getRisks();
      set({ risks: data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchInsights: async () => {
    try {
      const data = await predictiveAPI.getInsights();
      set({ insights: data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  fetchSuggestions: async () => {
    try {
      const data = await predictiveAPI.getSuggestions();
      set({ suggestions: data });
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  dismissSuggestion: async (id: string) => {
    try {
      await predictiveAPI.dismissSuggestion(id);
      set(state => ({
        suggestions: state.suggestions.filter(s => s.id !== id),
      }));
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  executeSuggestion: async (id: string) => {
    try {
      const result = await predictiveAPI.executeSuggestion(id);
      set(state => ({
        suggestions: state.suggestions.filter(s => s.id !== id),
      }));
      return result;
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },
}));
