import { create } from 'zustand';
import { latticesAPI, LatticeNode, LatticeEdge } from '../api/lattices';

interface LatticeState {
  nodes: LatticeNode[];
  edges: LatticeEdge[];
  isLoading: boolean;
  error: string | null;
  fetchLattices: () => Promise<void>;
}

export const useLatticeStore = create<LatticeState>((set) => ({
  nodes: [],
  edges: [],
  isLoading: false,
  error: null,

  fetchLattices: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await latticesAPI.getLattices();
      set({ 
        nodes: data.nodes, 
        edges: data.edges, 
        isLoading: false 
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },
}));
