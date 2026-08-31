import { api } from './api';

export const memoryService = {
  getLattice: () => api.get('/thermodynamics/lattice'),
};
