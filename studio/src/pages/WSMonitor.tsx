import React from 'react';
import { useWSMonitorQuery } from '../hooks/query/useWSMonitorQuery';

export const WSMonitor: React.FC = () => {
  const { data, isLoading, error } = useWSMonitorQuery();

  if (isLoading) return <div>Loading WebSocket Monitor...</div>;
  if (error) return <div>Error: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div>
      <h1>WebSocket Monitor</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
};
