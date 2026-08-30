import { api } from './api';

export const temporalService = {
  getMetrics: (params: any) => api.get('/api/v1/dashboard/metrics', { params }),
  search: (params: any) => api.get('/api/v1/search', { params }),
  getTemporalInsights: () => api.get('/api/v1/temporal/metrics')
};
