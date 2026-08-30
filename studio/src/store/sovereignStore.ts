import { create } from 'zustand';

export type ExecutionMode = 'standard' | 'restricted' | 'simulation' | 'audit';

interface SovereignState {
  executionMode: ExecutionMode;
  airGapped: boolean;
  dataSovereigntyLevel: 'local' | 'hybrid' | 'cloud';
  setMode: (mode: ExecutionMode) => void;
  toggleAirGapped: () => void;
  setSovereignty: (level: 'local' | 'hybrid' | 'cloud') => void;
}

export const useSovereignStore = create<SovereignState>((set) => ({
  executionMode: 'standard',
  airGapped: false,
  dataSovereigntyLevel: 'local',
  setMode: (mode) => set({ executionMode: mode }),
  toggleAirGapped: () => set((state) => ({ airGapped: !state.airGapped })),
  setSovereignty: (level) => set({ dataSovereigntyLevel: level }),
}));
