import React from 'react';
import styles from './MetricCard.module.css';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon?: string;
  trend?: 'up' | 'down' | 'stable';
  format?: 'number' | 'percentage' | 'currency';
  status?: 'success' | 'warning' | 'danger' | 'stable';
  progress?: number;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  trend,
  format = 'number',
  status = 'stable',
  progress,
}) => {
  const formattedValue = format === 'percentage' 
    ? `${(typeof value === 'number' ? (value * 100).toFixed(1) : value)}%`
    : format === 'currency'
    ? `$${value}`
    : value;

  const trendIcon = trend === 'up' ? '📈' : trend === 'down' ? '📉' : '➡️';

  return (
    <div className={`${styles.card} ${styles[status]}`}>
      <div className={styles.header}>
        {icon && <span className={styles.icon}>{icon}</span>}
        <span className={styles.title}>{title}</span>
      </div>
      <div className={styles.value}>{formattedValue}</div>
      {trend && (
        <div className={styles.trend}>
          <span className={styles.trendIcon}>{trendIcon}</span>
          <span className={styles.trendLabel}>
            {trend === 'up' ? 'Increasing' : trend === 'down' ? 'Decreasing' : 'Stable'}
          </span>
        </div>
      )}
      {progress !== undefined && (
        <div className={styles.progressBar}>
          <div 
            className={styles.progressFill}
            style={{ width: `${Math.min(progress * 100, 100)}%` }}
          />
        </div>
      )}
    </div>
  );
};
