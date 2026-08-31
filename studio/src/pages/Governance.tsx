import React from 'react';
import { Link } from 'react-router-dom';
import { useGovernanceQuery } from '../hooks/query/useGovernanceQuery';

export const Governance: React.FC = () => {
  const { data, isLoading, error } = useGovernanceQuery();

  if (isLoading) return <div>Loading Governance Center...</div>;
  if (error) return <div>Error loading Governance Center: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className="governance-container">
      <h1>Governance Center</h1>
      <div className="governance-nav">
        <Link to="/governance/policies">Policy Management</Link>
        <br />
        <Link to="/governance/constitution">Constitution Editor</Link>
      </div>
      <div className="governance-content">
        <h2>Overview</h2>
        <pre>{JSON.stringify(data, null, 2)}</pre>
      </div>
    </div>
  );
};
