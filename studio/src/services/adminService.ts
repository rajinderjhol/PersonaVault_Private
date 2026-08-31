// studio/src/services/adminService.ts
import { apiClient } from '../api/client';

export const adminService = {
  getUsers: () => apiClient.get('/api/v1/admin/users'),
  createUser: (userData: any) => apiClient.post('/api/v1/admin/users', userData),
  updateUser: (userId: string, userData: any) => apiClient.put(`/api/v1/admin/users/${userId}`, userData),
  deleteUser: (userId: string) => apiClient.delete(`/api/v1/admin/users/${userId}`),
  getRoles: () => apiClient.get('/api/v1/admin/roles'),
  createRole: (roleData: any) => apiClient.post('/api/v1/admin/roles', roleData),
  updateRole: (roleId: string, roleData: any) => apiClient.put(`/api/v1/admin/roles/${roleId}`, roleData),
  deleteRole: (roleId: string) => apiClient.delete(`/api/v1/admin/roles/${roleId}`),
};
