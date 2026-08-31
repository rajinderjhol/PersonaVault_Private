import React from 'react';
import { useSecurityQuery } from '../hooks/query/useSecurityQuery';

export const SecurityCenter: React.FC = () => {
  const { data, isLoading, error } = useSecurityQuery();

  if (isLoading) return <div>Loading Security Center...</div>;
  if (error) return <div>Error loading Security Center: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="security-container">
      <h1>Security Center</h1>
      <div className="security-content">
        <h2>Intelligence</h2>
        <pre>{JSON.stringify(data?.intelligence, null, 2)}</pre>
        <h2>Recent Events</h2>
        <pre>{JSON.stringify(data?.events, null, 2)}</pre>
      </div>
    </div>
  );
};
