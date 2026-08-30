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
    const response = await apiClient.post('/auth/login', { username, password });
    return response.data;
  },
  
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout');
  },
  
  getMe: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },
};
