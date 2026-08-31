import React from 'react';
import { useAdminQuery } from '../../hooks/query/useAdminQuery';

export const RoleManagement: React.FC = () => {
  const { rolesQuery } = useAdminQuery();
  const { data, isLoading, error } = rolesQuery;

  if (isLoading) return <div>Loading Roles...</div>;
  if (error) return <div>Error: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div>
      <h1>Role Management</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};
