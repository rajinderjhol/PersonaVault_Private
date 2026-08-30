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
    const response = await apiClient.get('/marketplace/packs');
    return response.data.packs || [];
  },

  getInstalled: async (): Promise<Pack[]> => {
    const response = await apiClient.get('/marketplace/installed');
    return response.data.packs || [];
  },

  installPack: async (packId: string): Promise<void> => {
    await apiClient.post(`/marketplace/packs/${packId}/install`);
  },

  uninstallPack: async (packId: string): Promise<void> => {
    await apiClient.post(`/marketplace/packs/${packId}/uninstall`);
  },
};
