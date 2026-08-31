import React from 'react';
import { useVerilinkQuery } from '../hooks/query/useVerilinkQuery';

export const VeriLinkStatus: React.FC = () => {
  const { data, isLoading, error } = useVerilinkQuery();

  if (isLoading) return <div>Loading VeriLink Status...</div>;
  if (error) return <div>Error loading VeriLink Status: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="verilink-container">
      <h1>VeriLink Status</h1>
      <div className="verilink-content">
        <p>Cryptographic provenance status.</p>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
