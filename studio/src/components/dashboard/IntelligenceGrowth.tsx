import React from 'react';
import { useV2GrowthMetrics, GrowthMetrics } from '../../hooks/query/v2/useV2GrowthMetrics';
import styles from './IntelligenceGrowth.module.css';

interface IntelligenceGrowthProps {
  data?: GrowthMetrics | null;
  isLoading?: boolean;
}

export const IntelligenceGrowth: React.FC<IntelligenceGrowthProps> = ({ data: externalData, isLoading: externalLoading }) => {
  const { data: hookData, isLoading: hookLoading } = useV2GrowthMetrics();
  const data = externalData !== undefined ? externalData : hookData;
  const isLoading = externalLoading !== undefined ? externalLoading : hookLoading;

  if (isLoading && !data) return <div className={styles.loading}>Loading growth data...</div>;
  if (!data) return null;

  const maxMemory = data.memoryHistory.length > 0 
    ? Math.max(...data.memoryHistory.map(m => m.count))
    : 100;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleInfo}>
          <span className={styles.icon}>📈</span>
          <span className={styles.title}>Intelligence Growth</span>
        </div>
        <span className={styles.badge}>
          {data.compressionRatio}:1 Compression
        </span>
      </div>
      
      <div className={styles.chartContainer}>
        <div className={styles.chart}>
          {data.memoryHistory.map((point, index) => (
            <div key={index} className={styles.barContainer}>
              <div 
                className={styles.bar}
                style={{ 
                  height: `${(point.count / maxMemory) * 100}%`,
                  backgroundColor: point.type === 'memory' ? '#4a90d9' : '#27ae60'
                }}
                title={`${point.type}: ${point.count}`}
              />
              <div className={styles.barLabel}>{point.date}</div>
            </div>
          ))}
        </div>
      </div>
      
      <div className={styles.stats}>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Total Memories</span>
          <span className={styles.statValue}>{data.totalMemories.toLocaleString()}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Crystallized</span>
          <span className={styles.statValue}>{data.crystallizedCount.toLocaleString()}</span>
        </div>
        <div className={styles.stat}>
          <span className={styles.statLabel}>Efficiency</span>
          <span className={styles.statValue}>{Math.round((data.crystallizedCount / data.totalMemories) * 100)}%</span>
        </div>
      </div>
    </div>
  );
};
