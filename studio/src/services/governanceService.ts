import { api } from './api';

export const governanceService = {
  getOverview: () => api.get('/governance/overview'),
};
