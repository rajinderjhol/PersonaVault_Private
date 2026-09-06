import React from 'react';
import { useV2Insights, IntelligenceInsight } from '../../../../hooks/query/v2/useV2Insights';
import styles from './IntelligenceInsights.module.css';

interface IntelligenceInsightsProps {
  insights?: IntelligenceInsight[] | null;
  isLoading?: boolean;
}

export const IntelligenceInsights: React.FC<IntelligenceInsightsProps> = ({ insights: externalInsights, isLoading: externalLoading }) => {
  const { data: hookData, isLoading: hookLoading } = useV2Insights();
  const insights = externalInsights !== undefined ? externalInsights : hookData;
  const isLoading = externalLoading !== undefined ? externalLoading : hookLoading;

  if (isLoading && !insights) return <div className={styles.loading}>Generating insights...</div>;
  if (!insights || insights.length === 0) return null;

  const getIcon = (type: IntelligenceInsight['type']) => {
    switch (type) {
      case 'security': return '🛡️';
      case 'optimization': return '⚡';
      case 'agent': return '🤖';
      case 'learning': return '🧠';
      default: return '💡';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <span className={styles.icon}>💡</span>
        <span className={styles.title}>Proactive Insights</span>
      </div>

      <div className={styles.list}>
        {insights.map((insight: IntelligenceInsight) => (
          <div key={insight.id} className={`${styles.card} ${styles[insight.priority]}`}>
            <div className={styles.cardHeader}>
              <span className={styles.typeIcon}>{getIcon(insight.type)}</span>
              <span className={styles.priorityLabel}>{insight.priority}</span>
            </div>
            <p className={styles.message}>{insight.message}</p>
            {insight.actionLabel && (
              <button className={styles.actionBtn}>
                {insight.actionLabel}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
