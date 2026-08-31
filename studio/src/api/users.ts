import { apiClient } from './client';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'viewer';
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export const usersAPI = {
  listUsers: async (): Promise<User[]> => {
    const data = await apiClient.get<any>('/admin/users');
    return data.users || [];
  },

  updateRole: async (userId: string, role: string): Promise<void> => {
    await apiClient.patch(`/admin/users/${userId}/role`, { role });
  },

  getRoles: async (): Promise<{ name: string; description: string }[]> => {
    const data = await apiClient.get<any>('/admin/roles');
    return data.roles || [];
  },
};
