// studio/src/services/modelService.ts
import { apiClient } from '../api/client';
export const modelService = {
  getModels: () => apiClient.get('/models'),
  addModel: (modelData: any) => apiClient.post('/api/v1/models/', modelData),
  updateModel: (modelId: string, modelData: any) => apiClient.put(`/api/v1/models/${modelId}/`, modelData),
  deleteModel: (modelId: string) => apiClient.delete(`/api/v1/models/${modelId}/`),
};
