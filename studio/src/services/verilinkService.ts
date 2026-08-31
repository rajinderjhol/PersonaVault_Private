import { api } from './api';

export const verilinkService = {
  getStatus: () => api.get('/verilink/status'),
};
