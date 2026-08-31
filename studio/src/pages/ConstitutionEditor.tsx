import React, { useState, useEffect } from 'react';
import { useConstitutionQuery, useUpdateConstitutionMutation } from '../hooks/query/useConstitutionQuery';

export const ConstitutionEditor: React.FC = () => {
  const { data, isLoading, error } = useConstitutionQuery();
  const updateMutation = useUpdateConstitutionMutation();
  const [content, setContent] = useState('');

  useEffect(() => {
    if (data) {
      setContent(JSON.stringify(data, null, 2));
    }
  }, [data]);

  if (isLoading) return <div>Loading Constitution...</div>;
  if (error) return <div>Error loading Constitution: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  const handleUpdate = () => {
    try {
      const parsedData = JSON.parse(content);
      updateMutation.mutate(parsedData);
    } catch (e) {
      alert('Invalid JSON format');
    }
  };

  return (
    <div className="constitution-container">
      <h1>Constitution Editor</h1>
      <textarea 
        value={content} 
        onChange={(e) => setContent(e.target.value)}
        rows={20}
        style={{ width: '100%', fontFamily: 'monospace' }}
      />
      <button onClick={handleUpdate} disabled={updateMutation.isPending}>
        {updateMutation.isPending ? 'Updating...' : 'Save Constitution'}
      </button>
    </div>
  );
};
