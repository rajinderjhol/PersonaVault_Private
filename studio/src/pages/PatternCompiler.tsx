import React from 'react';
import { useCompilerQuery } from '../hooks/query/useCompilerQuery';

export const PatternCompiler: React.FC = () => {
  const { data, isLoading, error } = useCompilerQuery();

  if (isLoading) return <div>Loading Pattern Compiler...</div>;
  if (error) return <div>Error loading Pattern Compiler: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="compiler-container">
      <h1>Pattern Compiler</h1>
      <div className="compiler-content">
        <p>Manage and compile Behaviour Packs here.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
