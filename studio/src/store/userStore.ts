import { create } from 'zustand';
import { usersAPI, User } from '../api/users';

interface UserState {
  users: User[];
  roles: { name: string; description: string }[];
  isLoading: boolean;
  error: string | null;
  fetchUsers: () => Promise<void>;
  updateUserRole: (userId: string, role: string) => Promise<void>;
  fetchRoles: () => Promise<void>;
}

export const useUserStore = create<UserState>((set, get) => ({
  users: [],
  roles: [],
  isLoading: false,
  error: null,

  fetchUsers: async () => {
    set({ isLoading: true });
    try {
      const users = await usersAPI.listUsers();
      set({ users, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch users', isLoading: false });
    }
  },

  updateUserRole: async (userId: string, role: string) => {
    try {
      await usersAPI.updateRole(userId, role);
      await get().fetchUsers();
    } catch (error) {
      set({ error: 'Failed to update user role' });
    }
  },

  fetchRoles: async () => {
    try {
      const roles = await usersAPI.getRoles();
      set({ roles });
    } catch (error) {
      set({ error: 'Failed to fetch roles' });
    }
  },
}));
