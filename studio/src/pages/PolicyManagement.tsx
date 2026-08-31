import React from 'react';
import { usePolicyQuery } from '../hooks/query/usePolicyQuery';

export const PolicyManagement: React.FC = () => {
  const { data, isLoading, error } = usePolicyQuery();

  if (isLoading) return <div>Loading Policies...</div>;
  if (error) return <div>Error loading Policies: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="policy-container">
      <h1>Policy Management</h1>
      <div className="policy-content">
        <p>Manage and version governance policies here.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
