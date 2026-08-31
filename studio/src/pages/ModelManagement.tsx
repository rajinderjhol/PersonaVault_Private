import React from 'react';
import { useModelQuery } from '../hooks/query/useModelQuery';

export const ModelManagement: React.FC = () => {
  const { modelsQuery } = useModelQuery();
  const { data, isLoading, error } = modelsQuery;

  if (isLoading) return <div>Loading Models...</div>;
  if (error) return <div>Error: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div>
      <h1>Model Management</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};
