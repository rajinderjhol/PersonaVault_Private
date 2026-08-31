import { api } from './api';

export const userService = {
  getProfile: () => api.get('/auth/me'),
  updateProfile: (data: any) => api.put('/users/me', data),
};
