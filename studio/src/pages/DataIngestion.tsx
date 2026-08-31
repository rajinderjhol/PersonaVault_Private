import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { ingestionApi } from '../services/ingestionService';
import { useJobStatusQuery } from '../hooks/query/useJobStatusQuery';
import styles from './DataIngestion.module.css';

export const DataIngestion: React.FC = () => {
  const [folderPath, setFolderPath] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (path: string) => ingestionApi.ingestFolder(path),
    onSuccess: (response) => {
      setJobId(response.data.job_id);
    }
  });

  const { data: jobStatus, isLoading: isPolling } = useJobStatusQuery(jobId);

  const handleIngest = () => {
    mutation.mutate(folderPath);
  };

  return (
    <div className={styles.container}>
      <h1>Bulk Data Ingestion</h1>
      <div className={styles.inputGroup}>
        <input 
          type="text" 
          value={folderPath} 
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Enter server folder path (e.g., /data/contracts)"
        />
        <button onClick={handleIngest} disabled={mutation.isPending}>
          {mutation.isPending ? 'Starting...' : 'Start Ingestion'}
        </button>
      </div>
      {jobId && (
        <div className={styles.statusBox}>
          <p>Job ID: {jobId}</p>
          <p>Status: <strong>{jobStatus?.status || 'processing'}</strong></p>
        </div>
      )}
    </div>
  );
};
