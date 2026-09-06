import React, { useState } from 'react';
import { useV2StartIngestion, useV2IngestionStatus, useV2Documents } from '../hooks/query/v2/useV2Ingestion';
import styles from './IntelligenceVault.module.css';

export const IntelligenceVault: React.FC = () => {
  const [folderPath, setFolderPath] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);
  const { mutate: startIngestion, isPending: isStarting } = useV2StartIngestion();
  const { data: documents, isLoading: isLoadingDocs } = useV2Documents();
  const { data: jobStatus } = useV2IngestionStatus(jobId);

  const handleStartIngestion = () => {
    if (!folderPath) return;
    startIngestion({ folderPath }, {
      onSuccess: (data) => {
        setJobId(data.job_id);
        setFolderPath('');
      }
    });
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🧠 Intelligence Vault</h1>
        <p>Ingest documents and manage your intelligence repository</p>
      </div>

      {/* Ingestion Form */}
      <div className={styles.ingestionSection}>
        <h2>📥 Data Ingestion</h2>
        <div className={styles.ingestionForm}>
          <input
            type="text"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            placeholder="Enter folder path (e.g., /data/contracts)"
            className={styles.pathInput}
          />
          <button 
            onClick={handleStartIngestion}
            disabled={!folderPath || isStarting}
            className={styles.ingestButton}
          >
            {isStarting ? '⏳ Starting...' : '🚀 Start Ingestion'}
          </button>
        </div>

        {jobId && (
          <div className={styles.jobStatus}>
            <h3>📊 Job Status</h3>
            <div className={styles.statusBar}>
              <span>Status: {jobStatus?.status || 'processing'}</span>
            </div>
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ width: `${(jobStatus?.successful_files || 0) / (jobStatus?.total_files || 1) * 100}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className={styles.documentsSection}>
        <h2>📄 Documents</h2>
        {isLoadingDocs ? (
          <div className={styles.loading}>Loading documents...</div>
        ) : (
          <div className={styles.documentsGrid}>
            {!documents || documents.length === 0 ? (
              <div className={styles.emptyState}>
                <span className={styles.emptyIcon}>📂</span>
                <p>No documents ingested yet</p>
                <p className={styles.emptySubtext}>Start by ingesting a folder above</p>
              </div>
            ) : (
              documents.map((doc: any) => (
                <div key={doc.id} className={styles.documentCard}>
                  <div className={styles.docIcon}>📄</div>
                  <div className={styles.docInfo}>
                    <span className={styles.docName}>{doc.name}</span>
                    <span className={styles.docType}>{doc.type}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
};
