import { apiClient } from './client';

export interface Pack {
  id: string;
  name: string;
  domain: string;
  version: string;
  description: string;
  status: 'available' | 'installed' | 'active';
  events: number;
  confidence: number;
  icon: string;
}

export const packsAPI = {
  listPacks: async (): Promise<Pack[]> => {
    const data = await apiClient.get<any>('/marketplace/packs');
    return data.packs || [];
  },

  getInstalled: async (): Promise<Pack[]> => {
    const data = await apiClient.get<any>('/marketplace/installed');
    return data.packs || [];
  },

  installPack: async (packId: string): Promise<void> => {
    await apiClient.post(`/marketplace/packs/${packId}/install`);
  },

  uninstallPack: async (packId: string): Promise<void> => {
    await apiClient.post(`/marketplace/packs/${packId}/uninstall`);
  },
};
