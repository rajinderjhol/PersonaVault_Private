import React from 'react';
import styles from './DashboardSkeleton.module.css';

export const DashboardSkeleton: React.FC = () => {
  return (
    <div className={styles.skeleton}>
      <div className={styles.header}>
        <div className={styles.titleSkeleton} />
      </div>
      <div className={styles.metricsGrid}>
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className={styles.metricCardSkeleton} />
        ))}
      </div>
    </div>
  );
};
