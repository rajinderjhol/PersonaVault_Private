// studio/src/hooks/query/useAdminQuery.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminService } from '../../services/adminService';

export const useAdminQuery = () => {
  const queryClient = useQueryClient();

  const usersQuery = useQuery({
    queryKey: ['admin', 'users'],
    queryFn: () => adminService.getUsers(),
    staleTime: 60000,
  });

  const rolesQuery = useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: () => adminService.getRoles(),
    staleTime: 60000,
  });

  const createUserMutation = useMutation({
    mutationFn: adminService.createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });

  const updateUserMutation = useMutation({
    mutationFn: ({ userId, userData }: { userId: string; userData: any }) =>
      adminService.updateUser(userId, userData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });

  const deleteUserMutation = useMutation({
    mutationFn: adminService.deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'users'] }),
  });

  const createRoleMutation = useMutation({
    mutationFn: adminService.createRole,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] }),
  });

  const updateRoleMutation = useMutation({
    mutationFn: ({ roleId, roleData }: { roleId: string; roleData: any }) =>
      adminService.updateRole(roleId, roleData),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] }),
  });

  const deleteRoleMutation = useMutation({
    mutationFn: adminService.deleteRole,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin', 'roles'] }),
  });

  return { usersQuery, rolesQuery, createUserMutation, updateUserMutation, deleteUserMutation, createRoleMutation, updateRoleMutation, deleteRoleMutation };
};
