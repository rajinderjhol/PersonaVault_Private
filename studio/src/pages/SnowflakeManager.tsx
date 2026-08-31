import React from 'react';
import { useSnowflakeQuery } from '../hooks/query/useSnowflakeQuery';

export const SnowflakeManager: React.FC = () => {
  const { data, isLoading, error } = useSnowflakeQuery();

  if (isLoading) return <div>Loading Snowflake Manager...</div>;
  if (error) return <div>Error loading Snowflake Manager: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="snowflake-container">
      <h1>Snowflake Manager</h1>
      <div className="snowflake-content">
        <p>Manage crystallized patterns here.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
