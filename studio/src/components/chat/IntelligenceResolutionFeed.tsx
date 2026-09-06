import React, { useState } from 'react';
import { IntelligenceResolution } from '../../api/chat';
import styles from './IntelligenceResolutionFeed.module.css';

interface Props {
  resolutions: IntelligenceResolution[];
  isStreaming?: boolean;
}

const PACK_COLORS: Record<string, string> = {
  'security': '#4A90D9',
  'compliance': '#27AE60',
  'contracts': '#9B59B6',
};

const LAYER_ICONS = {
  1: '💨',
  2: '💧',
  3: '🧊',
};

const getPackIcon = (packId: string): string => {
  const icons: Record<string, string> = {
    'security': '🛡️',
    'compliance': '⚖️',
    'contracts': '📜',
    'procurement': '📦',
    'insurance': '🛡️',
    'robotics': '🤖',
  };
  return icons[packId] || '📌';
};

export const IntelligenceResolutionFeed: React.FC<Props> = ({ 
  resolutions, 
  isStreaming 
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  if (!resolutions || resolutions.length === 0) return null;

  const totalPolicies = resolutions.reduce((sum, r) => sum + r.policies.count, 0);
  const totalMemories = resolutions.reduce(
    (sum, r) => sum + r.memories.reduce((s, m) => s + m.count, 0), 0
  );

  return (
    <div className={styles.container}>
      <div className={styles.header} onClick={() => setIsExpanded(!isExpanded)}>
        <div className={styles.headerLeft}>
          <span className={styles.icon}>📚</span>
          <span className={styles.title}>Intelligence Resolved</span>
          {isStreaming && <span className={styles.loading}>⏳ Resolving...</span>}
        </div>
        <div className={styles.headerRight}>
          <span className={styles.summary}>
            {totalPolicies} policies, {totalMemories} memories
          </span>
          <span className={styles.toggle}>{isExpanded ? '▼' : '▶'}</span>
        </div>
      </div>

      {isExpanded && (
        <div className={styles.content}>
          <div className={styles.intro}>While the system was analyzing your request:</div>
          
          {resolutions.map((resolution) => (
            <div 
              key={resolution.packId}
              className={styles.packGroup}
              style={{ borderLeftColor: PACK_COLORS[resolution.packId] || '#666' }}
            >
              <div className={styles.packHeader}>
                <span className={styles.packIcon}>{getPackIcon(resolution.packId)}</span>
                <span className={styles.packName}>{resolution.packName}</span>
              </div>
              
              <div className={styles.resolutionItems}>
                {resolution.policies.count > 0 && (
                  <div className={styles.resolutionItem}>
                    <span className={styles.itemIcon}>📋</span>
                    <span>
                      Found <strong>{resolution.policies.count}</strong> relevant 
                      polic{resolution.policies.count > 1 ? 'ies' : 'y'}
                      {resolution.policies.matched && (
                        <span className={styles.policyNames}>: {resolution.policies.matched.join(', ')}</span>
                      )}
                    </span>
                  </div>
                )}
                
                {resolution.memories.map((memory) => (
                  <div key={`${resolution.packId}-${memory.layer}`} className={styles.resolutionItem}>
                    <span className={styles.itemIcon}>{LAYER_ICONS[memory.layer]}</span>
                    <span>
                      Retrieved <strong>{memory.count}</strong> memory{memory.count > 1 ? 'ies' : ''} 
                      {' '}(Layer {memory.layer})
                      {memory.summary && <span className={styles.memorySummary}>: {memory.summary}</span>}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
          
          <div className={styles.footer}>
            <span className={styles.performance}>⏱️ Resolved in 1.2s</span>
          </div>
        </div>
      )}
    </div>
  );
};
