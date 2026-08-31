import { api } from './api';

export const crystallizationService = {
  getMetrics: () => api.get('/thermodynamics/crystallization'),
};
