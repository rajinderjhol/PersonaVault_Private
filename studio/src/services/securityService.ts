import { api } from './api';

export const securityService = {
  getSecurityEvents: () => api.get('/security/events'),
  getSecurityIntelligence: () => api.get('/security/intelligence'),
};
