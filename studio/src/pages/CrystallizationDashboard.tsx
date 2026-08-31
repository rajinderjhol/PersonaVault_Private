import React from 'react';
import { useCrystallizationQuery } from '../hooks/query/useCrystallizationQuery';

export const CrystallizationDashboard: React.FC = () => {
  const { data, isLoading, error } = useCrystallizationQuery();

  if (isLoading) return <div>Loading Crystallization Dashboard...</div>;
  if (error) return <div>Error loading Crystallization Dashboard: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="crystallization-container">
      <h1>Crystallization Dashboard</h1>
      <div className="crystallization-content">
        <p>Visualizing intelligence compression metrics.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
