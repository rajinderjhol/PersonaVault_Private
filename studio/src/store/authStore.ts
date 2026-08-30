import { create } from 'zustand';
import axios from 'axios';

axios.defaults.withCredentials = true;

interface User {
  id: number;
  username: string;
  role: string;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isAuthenticating: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isAuthenticating: true,
  error: null,

  login: async (username, password) => {
    set({ isAuthenticating: true, error: null });
    try {
      const response = await axios.post('/api/v1/auth/login', { username, password });
      if (response.data.status === 'success') {
        set({ 
          user: response.data.user, 
          isAuthenticated: true, 
          isAuthenticating: false 
        });
      }
    } catch (err: any) {
      set({ 
        error: err.response?.data?.detail || 'Login failed', 
        isAuthenticating: false 
      });
    }
  },

  logout: async () => {
    try {
      await axios.post('/api/v1/auth/logout');
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      set({ user: null, isAuthenticated: false });
    }
  },

  checkAuth: async () => {
    set({ isAuthenticating: true });
    try {
      const response = await axios.get('/api/v1/auth/me');
      set({ 
        user: response.data, 
        isAuthenticated: true, 
        isAuthenticating: false 
      });
    } catch (err: any) {
      console.error('Auth check error:', err);
      set({ user: null, isAuthenticated: false, isAuthenticating: false });
    }
  }
}));
