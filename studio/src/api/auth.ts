import { apiClient } from './client';

export interface LoginResponse {
  status: string;
  user: {
    id: number;
    username: string;
    role: string;
  };
  token?: string;
}

export const authAPI = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    return await apiClient.post('/auth/login', { username, password });
  },
  
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },
  
  getMe: async () => {
    return await apiClient.get('/auth/me');
  },
};
