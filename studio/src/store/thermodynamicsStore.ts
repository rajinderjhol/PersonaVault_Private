import { create } from 'zustand';

export type MemoryPhase = 'gas' | 'liquid' | 'ice' | 'snowflake';

interface ThermodynamicState {
  phases: {
    gas: number; // 0-100%
    liquid: number;
    ice: number;
    snowflake: number;
  };
  transitions: string[];
  setPhase: (phase: MemoryPhase, value: number) => void;
  addTransition: (log: string) => void;
}

export const useThermodynamicsStore = create<ThermodynamicState>((set) => ({
  phases: {
    gas: 85,
    liquid: 45,
    ice: 12,
    snowflake: 4
  },
  transitions: [
    'Freeze: Interaction #821 crystallized into Pattern #42',
    'Melt: Pattern #12 returned to working context',
    'Sublimate: Phase transition detected in Robotics Pack'
  ],
  setPhase: (phase, value) => set((state) => ({
    phases: { ...state.phases, [phase]: value }
  })),
  addTransition: (log) => set((state) => ({
    transitions: [log, ...state.transitions.slice(0, 4)]
  })),
}));
