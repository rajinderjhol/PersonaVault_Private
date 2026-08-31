// studio/src/services/marketplaceService.ts
import { api } from './api';

export const marketplaceService = {
  getMarketplaceItems: () => api.get('/marketplace/packs'),
  installItem: (itemId: string) => api.post(`/marketplace/packs/${itemId}/install`, {}),
};
