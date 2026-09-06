import React from 'react';
import styles from './ProviderStats.module.css';

interface ProviderStatsProps {
  stats: any; // Ideally typed based on backend response
}

export const ProviderStats: React.FC<ProviderStatsProps> = ({ stats }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>📊 Provider Status</h3>
      <div className={styles.statsGrid}>
        {stats && Object.entries(stats).map(([provider, data]: [string, any]) => (
          <div key={provider} className={styles.statItem}>
            <div className={styles.providerName}>{provider}</div>
            <div className={styles.statDetails}>
              <span>Reqs: {data.requests || 'N/A'}</span>
              <span>Tokens: {data.tokens || 'N/A'}</span>
            </div>
            <div className={styles.status}>Status: {data.status || 'OK'}</div>
          </div>
        ))}
      </div>
      <button className={styles.refreshBtn}>🔄 Refresh Stats</button>
    </div>
  );
};
