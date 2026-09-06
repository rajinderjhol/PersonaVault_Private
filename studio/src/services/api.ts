// studio/src/services/api.ts
import { apiClient } from '../api/client';

export const api = apiClient;

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getDecisions: (params?: any) => api.get('/decisions', { params }),
  getTrends: (timeframe?: string) => api.get(`/dashboard/trends`, { params: { timeframe: timeframe || 'week' } }),
  getPatterns: () => api.get('/patterns/recent'),
};

export default api;
