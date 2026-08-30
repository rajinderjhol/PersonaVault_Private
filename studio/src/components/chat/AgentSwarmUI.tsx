import React, { useState, useEffect } from 'react';
import styles from './AgentSwarmUI.module.css';

interface TemporalContext {
  startDate: string;
  endDate: string;
  intervalType: string;
  originalExpression?: string;
  daysSpan?: number;
}

interface AgentMessage {
  id: string;
  agentName: string;
  content: string;
  timestamp: string;
  temporalContext?: TemporalContext;
}

interface AgentSwarmUIProps {
    messages: AgentMessage[];
    temporalContext?: TemporalContext;
}

export const AgentSwarmUI: React.FC<AgentSwarmUIProps> = ({ messages, temporalContext }) => {
  const [expanded, setExpanded] = useState<boolean>(true);
  
  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className={styles.agentSwarmUI}>
      <div className={styles.swarmHeader} onClick={() => setExpanded(!expanded)}>
        <div className={styles.swarmTitle}>
          <span className={styles.swarmIcon}>🐝</span>
          <span>Agent Swarm</span>
          <span className={styles.agentCount}>{messages.length} agents</span>
        </div>
        
        <div className={styles.swarmControls}>
          {temporalContext && (
            <div className={styles.temporalIndicator} title="Temporal filter active">
              <span className={styles.timeIcon}>🕐</span>
              <span className={styles.timeRange}>
                {formatDate(temporalContext.startDate)} - {formatDate(temporalContext.endDate)}
              </span>
            </div>
          )}
          <button className={styles.expandBtn}>
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>
      
      {/* Expanded content logic... */}
    </div>
  );
};
