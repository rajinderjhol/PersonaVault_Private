import React, { useState } from 'react';
import { useV2StartIngestion, useV2IngestionStatus } from '../hooks/query/v2/useV2Ingestion';
import styles from './DataIngestion.module.css';

export const DataIngestion: React.FC = () => {
  const [folderPath, setFolderPath] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const { mutate: startIngestion, isPending: isStarting } = useV2StartIngestion();
  const { data: jobStatus } = useV2IngestionStatus(jobId);

  const handleIngest = () => {
    startIngestion(folderPath, {
      onSuccess: (data) => {
        setJobId(data.job_id);
      }
    });
  };

  return (
    <div className={styles.container}>
      <h1>Bulk Data Ingestion (V2)</h1>
      <div className={styles.inputGroup}>
        <input 
          type="text" 
          value={folderPath} 
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="Enter server folder path (e.g., /data/contracts)"
        />
        <button onClick={handleIngest} disabled={isStarting}>
          {isStarting ? 'Starting...' : 'Start Ingestion'}
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
