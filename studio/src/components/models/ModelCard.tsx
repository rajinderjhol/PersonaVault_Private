import React from 'react';
import styles from './ModelCard.module.css';

interface ModelCardProps {
  model: {
    id: string;
    name: string;
    provider: string;
    size: string;
    confidence: number;
    latency: number;
    isActive: boolean;
    usedIn: string[];
    status: 'active' | 'available' | 'downloading' | 'error';
  };
  isActive: boolean;
  onSetActive: (id: string) => void;
  onDelete: (id: string) => void;
}

export const ModelCard: React.FC<ModelCardProps> = ({ 
  model, 
  isActive, 
  onSetActive, 
  onDelete 
}) => {
  return (
    <div className={styles.card}>
      <div className={styles.cardHeader}>
        <span className={styles.modelName}>{model.name}</span>
        <span className={styles.provider}>{model.provider}</span>
      </div>
      <div className={styles.cardMetrics}>
        <div className={styles.metric}>
          <span className={styles.label}>Status</span>
          <span className={`${styles.value} ${styles[model.status]}`}>{model.status}</span>
        </div>
        <div className={styles.metric}>
          <span className={styles.label}>Size</span>
          <span className={styles.value}>{model.size}</span>
        </div>
      </div>
      <div className={styles.cardActions}>
        {!isActive && (
          <button className={styles.actionBtn} onClick={() => onSetActive(model.id)}>Activate</button>
        )}
        <button className={styles.deleteBtn} onClick={() => onDelete(model.name)}>Delete</button>
      </div>
    </div>
  );
};
