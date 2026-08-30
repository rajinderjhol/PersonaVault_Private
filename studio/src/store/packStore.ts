import { create } from 'zustand';
import { packsAPI, Pack } from '../api/packs';

interface PackState {
  packs: Pack[];
  installedPacks: Pack[];
  isLoading: boolean;
  error: string | null;
  fetchPacks: () => Promise<void>;
  installPack: (id: string) => Promise<void>;
  uninstallPack: (id: string) => Promise<void>;
}

export const usePackStore = create<PackState>((set, get) => ({
  packs: [],
  installedPacks: [],
  isLoading: false,
  error: null,

  fetchPacks: async () => {
    set({ isLoading: true });
    try {
      const packs = await packsAPI.listPacks();
      const installed = await packsAPI.getInstalled();
      set({ packs, installedPacks: installed, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch packs', isLoading: false });
    }
  },

  installPack: async (id: string) => {
    try {
      await packsAPI.installPack(id);
      await get().fetchPacks();
    } catch (error) {
      set({ error: 'Failed to install pack' });
    }
  },

  uninstallPack: async (id: string) => {
    try {
      await packsAPI.uninstallPack(id);
      await get().fetchPacks();
    } catch (error) {
      set({ error: 'Failed to uninstall pack' });
    }
  },
}));
