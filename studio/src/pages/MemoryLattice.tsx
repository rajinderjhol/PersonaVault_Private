import React from 'react';
import { useMemoryQuery } from '../hooks/query/useMemoryQuery';

export const MemoryLattice: React.FC = () => {
  const { data, isLoading, error } = useMemoryQuery();

  if (isLoading) return <div>Loading Memory Lattice...</div>;
  if (error) return <div>Error loading Memory Lattice: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="memory-container">
      <h1>Memory Lattice Viewer</h1>
      <div className="memory-content">
        <p>Visualizing Gas, Liquid, and Ice memory layers.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
