import { useEffect } from 'react';
import { useUserStore } from '../store/userStore';

export const useUsers = () => {
  const { users, roles, isLoading, error, fetchUsers, updateUserRole, fetchRoles } = useUserStore();

  useEffect(() => {
    fetchUsers();
    fetchRoles();
  }, [fetchUsers, fetchRoles]);

  return {
    users,
    roles,
    isLoading,
    error,
    updateUserRole,
  };
};
