import React, { useState } from 'react';
import { useApiExplorerMutation } from '../hooks/query/useApiExplorerQuery';

export const APIExplorer: React.FC = () => {
  const [method, setMethod] = useState<'GET' | 'POST' | 'PUT' | 'DELETE'>('GET');
  const [path, setPath] = useState('');
  const [data, setData] = useState('');
  const mutation = useApiExplorerMutation();

  const handleExecute = () => {
    let parsedData = undefined;
    if (data) {
      try {
        parsedData = JSON.parse(data);
      } catch (e) {
        alert('Invalid JSON');
        return;
      }
    }
    mutation.mutate({ method, path, data: parsedData });
  };

  return (
    <div className="api-explorer-container">
      <h1>API Explorer</h1>
      <select value={method} onChange={(e) => setMethod(e.target.value as any)}>
        <option>GET</option>
        <option>POST</option>
        <option>PUT</option>
        <option>DELETE</option>
      </select>
      <input value={path} onChange={(e) => setPath(e.target.value)} placeholder="/api/v1/..." />
      <textarea value={data} onChange={(e) => setData(e.target.value)} placeholder="JSON payload (for POST/PUT)" />
      <button onClick={handleExecute} disabled={mutation.isPending}>
        {mutation.isPending ? 'Executing...' : 'Execute'}
      </button>
      <div className="api-explorer-response">
        <h2>Response</h2>
        <pre>{mutation.data ? JSON.stringify(mutation.data, null, 2) : mutation.error ? String(mutation.error) : 'No response yet'}</pre>
      </div>
    </div>
  );
};
