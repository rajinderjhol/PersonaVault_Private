import React from 'react';
import { useHealthQuery } from '../hooks/query/useHealthQuery';

export const SystemHealth: React.FC = () => {
  const { data, isLoading, error } = useHealthQuery();

  if (isLoading) return <div>Loading System Health...</div>;
  if (error) return <div>Error loading System Health: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="health-container">
      <h1>System Health Dashboard</h1>
      <div className="health-content">
        <h2>System Status</h2>
        <pre>{JSON.stringify(data?.health, null, 2)}</pre>
        <h2>Metrics</h2>
        <pre>{JSON.stringify(data?.metrics, null, 2)}</pre>
      </div>
    </div>
  );
};
