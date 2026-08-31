import { api } from './api';

export const trustService = {
  getDevices: () => api.get('/trust/devices'),
  getSyncStatus: () => api.get('/trust/sync'),
};
