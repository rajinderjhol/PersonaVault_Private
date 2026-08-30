import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authAPI } from '../api/auth';

interface User {
  id: number;
  username: string;
  role: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isAuthenticating: boolean;
  error: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isAuthenticating: true,
      error: null,

      login: async (username, password) => {
        set({ isAuthenticating: true, error: null });
        try {
          const data = await authAPI.login(username, password);
          set({ 
            user: data.user, 
            isAuthenticated: true, 
            isAuthenticating: false 
          });
        } catch (err: any) {
          set({ 
            error: err.response?.data?.detail || 'Login failed', 
            isAuthenticating: false 
          });
        }
      },

      logout: async () => {
        try {
          await authAPI.logout();
        } catch (err) {
          console.error('Logout error:', err);
        } finally {
          set({ user: null, token: null, isAuthenticated: false });
        }
      },

      checkAuth: async () => {
        set({ isAuthenticating: true });
        try {
          const user = await authAPI.getMe();
          set({ 
            user, 
            isAuthenticated: true, 
            isAuthenticating: false 
          });
        } catch (err: any) {
          console.error('Auth check error:', err);
          set({ user: null, token: null, isAuthenticated: false, isAuthenticating: false });
        }
      }
    }),
    { name: 'auth-storage' }
  )
);
