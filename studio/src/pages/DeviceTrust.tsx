import React from 'react';
import { useTrustQuery } from '../hooks/query/useTrustQuery';

export const DeviceTrust: React.FC = () => {
  const { data, isLoading, error } = useTrustQuery();

  if (isLoading) return <div>Loading Device Trust...</div>;
  if (error) return <div>Error loading Device Trust: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="trust-container">
      <h1>Device Trust</h1>
      <div className="trust-content">
        <h2>Devices</h2>
        <pre>{JSON.stringify(data?.devices, null, 2)}</pre>
        <h2>Sync Status</h2>
        <pre>{JSON.stringify(data?.syncStatus, null, 2)}</pre>
      </div>
    </div>
  );
};
