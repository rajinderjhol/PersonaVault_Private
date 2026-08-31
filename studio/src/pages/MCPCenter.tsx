import React from 'react';
import { useMCPQuery } from '../hooks/query/useMCPQuery';

export const MCPCenter: React.FC = () => {
  const { data, isLoading, error } = useMCPQuery();

  if (isLoading) return <div>Loading MCP Center...</div>;
  if (error) return <div>Error loading MCP Center: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="mcp-container">
      <h1>MCP Center</h1>
      <div className="mcp-content">
        <h2>Servers</h2>
        <pre>{JSON.stringify(data?.servers, null, 2)}</pre>
        <h2>Clients</h2>
        <pre>{JSON.stringify(data?.clients, null, 2)}</pre>
      </div>
    </div>
  );
};
