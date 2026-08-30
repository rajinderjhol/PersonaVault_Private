import { create } from 'zustand';
import { tracesAPI, Trace, TraceDetail } from '../api/traces';

interface TracesState {
  // State
  recentTraces: Trace[];
  sessionTraces: Trace[];
  currentTrace: TraceDetail | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Actions
  fetchRecent: () => Promise<void>;
  fetchSessionTraces: (sessionId: number) => Promise<void>;
  fetchTrace: (traceId: string) => Promise<void>;
  crystallize: (traceId: string) => Promise<void>;
  clearCurrentTrace: () => void;
  refreshAll: () => Promise<void>;
}

export const useTracesStore = create<TracesState>((set, get) => ({
  // Initial state
  recentTraces: [],
  sessionTraces: [],
  currentTrace: null,
  isLoading: false,
  error: null,
  lastUpdated: null,

  // Fetch recent traces
  fetchRecent: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await tracesAPI.getRecent(10);
      set({ recentTraces: data, isLoading: false, lastUpdated: new Date().toISOString() });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Fetch session traces
  fetchSessionTraces: async (sessionId: number) => {
    set({ isLoading: true, error: null });
    try {
      const data = await tracesAPI.getSessionTraces(sessionId);
      set({ sessionTraces: data, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Fetch single trace
  fetchTrace: async (traceId: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await tracesAPI.getTrace(traceId);
      set({ currentTrace: data, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Crystallize
  crystallize: async (traceId: string) => {
    try {
      await tracesAPI.crystallize(traceId);
      // Refresh recent traces to show updated state
      await get().fetchRecent();
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },

  // Clear current trace
  clearCurrentTrace: () => {
    set({ currentTrace: null });
  },

  // Refresh all
  refreshAll: async () => {
    await get().fetchRecent();
  },
}));
