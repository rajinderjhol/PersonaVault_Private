import React, { useState } from 'react';
import { DecisionGate as DecisionGateType } from '../../api/chat';
import { VERDICT_CONFIG } from './verdictConfig';
import { DecisionTimeline } from './DecisionTimeline';
import styles from './DecisionGate.module.css';

interface Props {
  decision: DecisionGateType;
  onReplay?: (decisionId: string) => void;
  onDownloadEvidence?: (decisionId: string) => void;
  onCopyId?: (decisionId: string) => void;
  isStreaming?: boolean;
}

export const DecisionGate: React.FC<Props> = ({
  decision,
  onReplay,
  onDownloadEvidence,
  onCopyId,
  isStreaming,
}) => {
  const [showTimeline, setShowTimeline] = useState(false);
  
  if (!decision) return null;

  const verdictConfig = VERDICT_CONFIG[decision.verdict] || VERDICT_CONFIG['REFUSED'];
  const isConsensus = decision.consensus.agreed === decision.consensus.total;
  const consensusPercentage = Math.round(
    (decision.consensus.agreed / decision.consensus.total) * 100
  );

  const handleReplay = () => onReplay?.(decision.decisionId);
  const handleDownload = () => onDownloadEvidence?.(decision.decisionId);
  const handleCopyId = () => {
    navigator.clipboard?.writeText(decision.decisionId);
    onCopyId?.(decision.decisionId);
  };

  return (
    <div 
      className={styles.container}
      style={{ borderLeftColor: verdictConfig.borderColor }}
    >
      <div className={styles.header}>
        <div 
          className={styles.verdictBadge}
          style={{ 
            backgroundColor: verdictConfig.bgColor,
            color: verdictConfig.color,
          }}
        >
          <span className={styles.verdictIcon}>{verdictConfig.icon}</span>
          <span className={styles.verdictLabel}>{verdictConfig.label}</span>
        </div>
        <div className={styles.reasonCode}>
          <span className={styles.reasonLabel}>Reason:</span>
          <span className={styles.reasonValue}>{decision.reasonCode}</span>
        </div>
        <div className={styles.timestamp}>
          {new Date(decision.timestamp).toLocaleTimeString()}
        </div>
      </div>

      <div className={styles.summary}>
        {decision.summary}
      </div>

      <div className={styles.consensus}>
        <div className={styles.consensusIcon}>
          {isConsensus ? '✅' : '⚠️'}
        </div>
        <div className={styles.consensusText}>
          <strong>{isConsensus ? 'Consensus' : 'Partial Consensus'}</strong>
          : {decision.consensus.agreed}/{decision.consensus.total} packs agreed 
          ({consensusPercentage}%)
        </div>
      </div>

      <div className={styles.timelineSection}>
        <button 
          className={styles.timelineToggle}
          onClick={() => setShowTimeline(!showTimeline)}
        >
          <span className={styles.timelineIcon}>📋</span>
          <span>View Decision Timeline</span>
          <span className={styles.timelineChevron}>
            {showTimeline ? '▼' : '▶'}
          </span>
        </button>
        
        {showTimeline && (
          <div className={styles.timelineContent}>
            <DecisionTimeline timeline={decision.timeline} />
          </div>
        )}
      </div>

      <div className={styles.actions}>
        {onDownloadEvidence && (
          <button 
            className={`${styles.actionButton} ${styles.primary}`}
            onClick={handleDownload}
          >
            📥 Download Evidence
          </button>
        )}
        {onReplay && (
          <button 
            className={`${styles.actionButton} ${styles.secondary}`}
            onClick={handleReplay}
          >
            🔄 Replay Decision
          </button>
        )}
        <button 
          className={`${styles.actionButton} ${styles.tertiary}`}
          onClick={handleCopyId}
        >
          📋 Copy ID
        </button>
      </div>

      {isStreaming && (
        <div className={styles.streamingIndicator}>
          ⏳ Finalizing decision...
        </div>
      )}
    </div>
  );
};
