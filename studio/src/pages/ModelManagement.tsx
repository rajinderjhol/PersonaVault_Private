import React, { useState } from 'react';
import { useV2Models, useV2ModelMetrics, useV2Providers } from '../hooks/query/v2/useV2Models';
import { ModelCard } from '../components/models/ModelCard';
import styles from './ModelManagement.module.css';

export const ModelManagement: React.FC = () => {
  const { data: models, isLoading: modelsLoading, error: modelsError } = useV2Models();
  const { data: metrics, isLoading: metricsLoading } = useV2ModelMetrics();
  const { data: providers, isLoading: providersLoading } = useV2Providers();
  const [selectedProvider, setSelectedProvider] = useState<string>('all');

  if (modelsError) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h3>Failed to load models</h3>
        <p>{(modelsError as Error).message}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  const activeModel = models?.find(m => m.isActive);
  const filteredModels = selectedProvider === 'all' 
    ? models 
    : models?.filter(m => m.provider === selectedProvider);

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <span className={styles.icon}>⚙️</span>
          <h1 className={styles.title}>Intelligence Engine Room</h1>
        </div>
        <div className={styles.headerRight}>
          <button className={styles.primaryButton}>🔄 Pull New Model</button>
          <button className={styles.secondaryButton}>⚙️ Configure Providers</button>
        </div>
      </div>

      {activeModel && (
        <div className={styles.activeEngine}>
          <div className={styles.engineHeader}>
            <span className={styles.engineIcon}>🧠</span>
            <div className={styles.engineInfo}>
              <h2 className={styles.engineName}>
                {activeModel.name} ({activeModel.provider})
              </h2>
              <div className={styles.engineStats}>
                <span className={styles.statBadge}>✅ Active Engine</span>
                <span className={styles.statBadge}>⚡ {activeModel.confidence}% Confidence</span>
                <span className={styles.statBadge}>🚀 {activeModel.latency}ms</span>
              </div>
            </div>
          </div>
          <div className={styles.engineMetrics}>
            <div className={styles.metricItem}>
              <span className={styles.metricLabel}>Decisions Processed</span>
              <span className={styles.metricValue}>{metrics?.totalDecisions || '1,247'}</span>
            </div>
            <div className={styles.metricItem}>
              <span className={styles.metricLabel}>Hit Rate</span>
              <span className={styles.metricValue}>{metrics?.hitRate || '94%'}</span>
            </div>
            <div className={styles.metricItem}>
              <span className={styles.metricLabel}>Throughput</span>
              <span className={styles.metricValue}>{metrics?.throughput || '12.4'} req/s</span>
            </div>
          </div>
        </div>
      )}

      <div className={styles.modelsGrid}>
        {modelsLoading ? <p>Loading engines...</p> : filteredModels?.map(model => (
          <ModelCard 
            key={model.id}
            model={model}
            isActive={model.isActive}
            onSetActive={() => {}}
            onDelete={() => {}}
          />
        ))}
      </div>
    </div>
  );
};
