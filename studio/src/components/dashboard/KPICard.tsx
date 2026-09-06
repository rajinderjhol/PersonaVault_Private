import React from 'react';
import styles from './KPICard.module.css';

interface KPICardProps {
  title: string;
  value: string;
  trend: string;
  trendDirection: 'up' | 'down' | 'stable';
}

export const KPICard: React.FC<KPICardProps> = ({ title, value, trend, trendDirection }) => (
  <div className={styles.card}>
    <div className={styles.title}>{title}</div>
    <div className={styles.value}>{value}</div>
    <div className={`${styles.trend} ${styles[trendDirection]}`}>
      {trendDirection === 'up' ? '▲' : trendDirection === 'down' ? '▼' : '▬'} {trend}
    </div>
  </div>
);
