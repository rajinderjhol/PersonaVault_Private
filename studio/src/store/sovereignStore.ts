import { create } from 'zustand';
import { modeAPI, ModeConfig } from '../api/mode';

type ExecutionMode = 'standard' | 'restricted' | 'simulation' | 'audit';

interface SovereignState {
  executionMode: ExecutionMode;
  airGapped: boolean;
  dataSovereigntyLevel: 'local' | 'hybrid' | 'cloud';
  modeConfig: ModeConfig | null;
  isLoading: boolean;
  error: string | null;
  
  fetchCurrentMode: () => Promise<void>;
  setMode: (mode: ExecutionMode) => Promise<void>;
  toggleAirGapped: () => void;
  setSovereignty: (level: 'local' | 'hybrid' | 'cloud') => void;
}

export const useSovereignStore = create<SovereignState>((set, get) => ({
  executionMode: 'standard',
  airGapped: false,
  dataSovereigntyLevel: 'local',
  modeConfig: null,
  isLoading: false,
  error: null,

  fetchCurrentMode: async () => {
    set({ isLoading: true });
    try {
      const modeConfig = await modeAPI.getCurrentMode();
      set({ 
        modeConfig, 
        executionMode: modeConfig.mode,
        isLoading: false 
      });
    } catch (error) {
      set({ error: 'Failed to fetch mode configuration', isLoading: false });
    }
  },

  setMode: async (mode: ExecutionMode) => {
    try {
      await modeAPI.setMode(mode);
      await get().fetchCurrentMode();
    } catch (error) {
      set({ error: 'Failed to switch mode' });
    }
  },
  
  toggleAirGapped: () => set((state) => ({ airGapped: !state.airGapped })),
  setSovereignty: (level) => set({ dataSovereigntyLevel: level }),
}));
