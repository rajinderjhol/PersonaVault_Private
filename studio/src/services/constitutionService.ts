import { api } from './api';

export const constitutionService = {
  getConstitution: () => api.get('/governance/constitution'),
  updateConstitution: (data: any) => api.put('/governance/constitution', data),
};
