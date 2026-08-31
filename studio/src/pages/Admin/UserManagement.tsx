import React from 'react';
import { useAdminQuery } from '../../hooks/query/useAdminQuery';

export const UserManagement: React.FC = () => {
  const { usersQuery } = useAdminQuery();
  const { data, isLoading, error } = usersQuery;

  if (isLoading) return <div>Loading Users...</div>;
  if (error) return <div>Error: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div>
      <h1>User Management</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};
