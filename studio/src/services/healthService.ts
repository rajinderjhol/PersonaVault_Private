import { api } from './api';

export const healthService = {
  getHealth: () => api.get('/admin/health'),
  getMetrics: () => api.get('/admin/metrics'),
};
