// studio/src/services/wsMonitorService.ts
import { apiClient } from '../api/client';

export const wsMonitorService = {
  getStatus: () => apiClient.get('/api/v1/ws/status'),
  getConnections: () => apiClient.get('/api/v1/ws/connections'),
};
