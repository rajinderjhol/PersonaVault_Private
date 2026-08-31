import { api } from './api';

export const policyService = {
  getPolicies: () => api.get('/governance/policies'),
  createPolicy: (data: any) => api.post('/governance/policies', data),
  updatePolicy: (id: string, data: any) => api.put(`/governance/policies/${id}`, data),
};
