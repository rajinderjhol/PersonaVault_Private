import React from 'react';
import { AgentAttribution } from './AgentAttribution';
import styles from './AttributionGroup.module.css';

interface Attribution {
  agentId: string;
  text?: string;
}

interface Props {
  attributions: Attribution[];
  variant?: 'inline' | 'stacked' | 'compact';
  showLabels?: boolean;
  onAgentClick?: (agentId: string) => void;
}

export const AttributionGroup: React.FC<Props> = ({
  attributions,
  variant = 'inline',
  showLabels = true,
  onAgentClick,
}) => {
  if (!attributions || attributions.length === 0) return null;

  if (variant === 'inline') {
    return (
      <span className={styles.inlineGroup}>
        {attributions.map((attr, index) => (
          <span key={attr.agentId} className={styles.inlineItem}>
            <AgentAttribution
              agentId={attr.agentId}
              size="small"
              variant="inline"
              onClick={onAgentClick}
            />
            {attr.text && (
              <span className={styles.inlineText}>{attr.text}</span>
            )}
            {index < attributions.length - 1 && (
              <span className={styles.inlineSeparator}>·</span>
            )}
          </span>
        ))}
      </span>
    );
  }

  if (variant === 'compact') {
    return (
      <div className={styles.compactGroup}>
        {attributions.map((attr) => (
          <AgentAttribution
            key={attr.agentId}
            agentId={attr.agentId}
            size="small"
            variant="badge"
            onClick={onAgentClick}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={styles.stackedGroup}>
      <div className={styles.stackedHeader}>
        <span className={styles.stackedIcon}>🤖</span>
        <span className={styles.stackedTitle}>Contributing Agents</span>
      </div>
      <div className={styles.stackedList}>
        {attributions.map((attr) => (
          <div key={attr.agentId} className={styles.stackedItem}>
            <AgentAttribution
              agentId={attr.agentId}
              size="medium"
              variant="badge"
              onClick={onAgentClick}
            />
            {attr.text && (
              <span className={styles.stackedText}>{attr.text}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
