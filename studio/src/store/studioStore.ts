import { create } from 'zustand';

interface StudioState {
  activePackIds: string[];
  metrics: {
    memoryHitRate: number;
    latency: number;
  };
  setActivePacks: (packIds: string[]) => void;
  addPack: (packId: string) => void;
  removePack: (packId: string) => void;
  setMetrics: (metrics: { memoryHitRate: number; latency: number }) => void;
}

export const useStudioStore = create<StudioState>((set) => ({
  activePackIds: [],
  metrics: {
    memoryHitRate: 0,
    latency: 0,
  },
  setActivePacks: (activePackIds) => set({ activePackIds }),
  addPack: (packId) =>
    set((state) => ({
      activePackIds: state.activePackIds.includes(packId)
        ? state.activePackIds
        : [...state.activePackIds, packId],
    })),
  removePack: (packId) =>
    set((state) => ({
      activePackIds: state.activePackIds.filter((id) => id !== packId),
    })),
  setMetrics: (metrics) => set({ metrics }),
}));
