import { api } from './api';

export const compilerService = {
  getPacks: () => api.get('/compiler/packs'),
  compilePack: (packId: string) => api.post(`/compiler/compile/${packId}`, {}),
};
