import React from 'react';
import { useSecurityQuery } from '../hooks/query/useSecurityQuery';
import styles from './SecurityCenter.module.css';

export const SecurityCenter: React.FC = () => {
  const { data, isLoading, error } = useSecurityQuery();

  if (isLoading) return <div className={styles.container}>Loading Security Center...</div>;
  if (error) return <div className={styles.container}>Error loading Security Center: {error instanceof Error ? error.message : 'Unknown error'}</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🛡️ Security Center</h1>
      </div>
      
      <div className={styles.content}>
        <div className={styles.card}>
          <h2>Intelligence Status</h2>
          <ul className={styles.dataList}>
            {data?.intelligence && Object.entries(data.intelligence).map(([key, value]) => (
              <li key={key} className={styles.dataItem}>
                <span className={styles.dataLabel}>{key.replace(/_/g, ' ')}</span>
                <span className={styles.dataValue}>{String(value)}</span>
              </li>
            ))}
          </ul>
        </div>
        
        <div className={styles.card}>
          <h2>Recent Security Events</h2>
          <ul className={styles.dataList}>
            {data?.events && data.events.map((event: any, index: number) => (
              <li key={index} className={styles.dataItem}>
                <span className={styles.dataLabel}>{new Date(event.timestamp).toLocaleTimeString()}</span>
                <span className={styles.dataValue}>{event.description || event.type}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};
