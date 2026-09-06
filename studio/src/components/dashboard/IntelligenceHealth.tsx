import React from 'react';
import { useV2Health, HealthMetric, SystemHealth } from '../../hooks/query/v2/useV2Health';
import styles from './IntelligenceHealth.module.css';

interface IntelligenceHealthProps {
  health?: SystemHealth | null;
  isLoading?: boolean;
}

export const IntelligenceHealth: React.FC<IntelligenceHealthProps> = ({ health, isLoading: externalLoading }) => {
  const { data: hookData, isLoading: hookLoading } = useV2Health();
  const data = health !== undefined ? health : hookData;
  const isLoading = externalLoading !== undefined ? externalLoading : hookLoading;

  if (isLoading && !data) return <div className={styles.loading}>Monitoring health...</div>;
  if (!data) return null;

  const getStatusColor = (status: HealthMetric['status']) => {
    switch (status) {
      case 'excellent': return '#22c55e';
      case 'healthy': return '#10b981';
      case 'good': return '#3b82f6';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleInfo}>
          <span className={styles.icon}>🛡️</span>
          <span className={styles.title}>System Health</span>
        </div>
        <span className={`${styles.statusBadge} ${styles[data.status]}`}>
          {data.status.toUpperCase()}
        </span>
      </div>

      <div className={styles.metricsGrid}>
        {data.metrics.map((metric, index) => (
          <div key={index} className={styles.metricCard}>
            <div className={styles.metricHeader}>
              <span className={styles.metricLabel}>{metric.label}</span>
              <span 
                className={styles.statusDot}
                style={{ backgroundColor: getStatusColor(metric.status) }}
              />
            </div>
            <div className={styles.metricValue}>{metric.value}</div>
            {metric.description && (
              <div className={styles.metricDesc}>{metric.description}</div>
            )}
          </div>
        ))}
      </div>

      <div className={styles.footer}>
        <span>v{data.version}</span>
        <span>Last updated: {new Date(data.timestamp).toLocaleTimeString()}</span>
      </div>
    </div>
  );
};
