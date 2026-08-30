import { create } from 'zustand';
import { trendsAPI, DomainTrend } from '../api/trends';

interface TrendState {
  trends: DomainTrend[];
  domains: string[];
  isLoading: boolean;
  error: string | null;
  fetchTrends: (domain?: string) => Promise<void>;
}

export const useTrendStore = create<TrendState>((set) => ({
  trends: [],
  domains: ['Security', 'Compliance', 'Contract', 'Procurement'],
  isLoading: false,
  error: null,

  fetchTrends: async (domain: string = 'confidence') => {
    set({ isLoading: true, error: null });
    try {
      const data = await trendsAPI.getTrends(domain);
      set({ trends: data, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
}));
