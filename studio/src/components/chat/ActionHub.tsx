import React, { useState } from 'react';
import { SuggestedAction } from '../../api/chat';
import styles from './ActionHub.module.css';

interface Props {
  actions: SuggestedAction[];
  decisionId?: string;
  verdict?: 'APPROVED' | 'CONTAINED' | 'ESCALATED' | 'REFUSED';
  onActionClick: (action: SuggestedAction) => void;
  isLoading?: boolean;
}

export const ActionHub: React.FC<Props> = ({
  actions,
  decisionId,
  onActionClick,
  isLoading = false,
}) => {
  const [executingActionId, setExecutingActionId] = useState<string | null>(null);

  if (!actions || actions.length === 0) return null;

  const handleActionClick = async (action: SuggestedAction) => {
    setExecutingActionId(action.id);
    try {
      await onActionClick(action);
    } finally {
      setExecutingActionId(null);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.headerIcon}>🎯</span>
        <span className={styles.headerTitle}>Recommended Actions</span>
        {decisionId && <span className={styles.decisionId}>ID: {decisionId.slice(0, 8)}</span>}
      </div>

      <div className={styles.actionsList}>
        {actions.map((action) => (
          <button
            key={action.id}
            className={`${styles.actionButton} ${action.primary ? styles.primary : ''}`}
            onClick={() => handleActionClick(action)}
            disabled={isLoading || executingActionId === action.id}
          >
            <div className={styles.actionContent}>
              <div className={styles.actionMain}>
                {action.icon && <span className={styles.actionIcon}>{action.icon}</span>}
                <span className={styles.actionLabel}>{action.label}</span>
                {action.primary && <span className={styles.actionBadge}>Primary</span>}
              </div>
              {action.description && <div className={styles.actionDescription}>→ {action.description}</div>}
            </div>
            {executingActionId === action.id && <span className={styles.loadingSpinner}>⏳</span>}
          </button>
        ))}
      </div>

      <div className={styles.footer}>
        <span className={styles.footerIcon}>📌</span>
        <span className={styles.footerText}>
          All actions are governed by policies and leave a traceable record.
        </span>
      </div>
    </div>
  );
};
