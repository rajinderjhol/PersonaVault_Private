import React, { useState } from 'react';
import { ingestionApi } from '../services/ingestionService';
import styles from './DataIngestion.module.css';

export const DataIngestion: React.FC = () => {
  const [folderPath, setFolderPath] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<string>('pending');
  const [loading, setLoading] = useState(false);

  const handleIngest = async () => {
    setLoading(true);
    try {
      const response = await ingestionApi.ingestFolder(folderPath);
      setJobId(response.data.job_id);
      setStatus('processing');
      
      // Start polling
      pollJobStatus(response.data.job_id);
    } catch (error) {
      console.error('Ingestion error:', error);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const pollJobStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await ingestionApi.getJobStatus(id);
        setStatus(response.data.status);
        if (response.data.status === 'completed' || response.data.status === 'failed') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error('Polling error:', error);
        clearInterval(interval);
        setStatus('error');
      }
    }, 2000);
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
        <button onClick={handleIngest} disabled={loading}>
          {loading ? 'Starting...' : 'Start Ingestion'}
        </button>
      </div>
      {jobId && (
        <div className={styles.statusBox}>
          <p>Job ID: {jobId}</p>
          <p>Status: <strong>{status}</strong></p>
        </div>
      )}
    </div>
  );
};
