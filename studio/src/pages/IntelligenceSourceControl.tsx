/**
 * Intelligence Source Control Page
 * V2 Studio - CSS Modules version (No Chakra UI)
 */

import React, { useState } from 'react';
import styles from '../components/modules/IntelligenceSourceControl/IntelligenceSourceControl.module.css';

// Types
interface TrustScoreHistory {
  timestamp: string;
  score: number;
  reason: string;
}

interface ContributionMetrics {
  patterns_crystallized: number;
  reasoning_steps_validated: number;
  memory_matches_contributed: number;
  decision_traces_triggered: number;
  events_ingested: number;
}

interface IntelligenceSource {
  id: string;
  name: string;
  type: 'endpoint' | 'iot' | 'agent' | 'behavior_pack';
  trust_score: number;
  trust_level: 'FULL' | 'HIGH' | 'MEDIUM' | 'BASIC' | 'UNTRUSTED';
  trust_history: TrustScoreHistory[];
  contribution_metrics: ContributionMetrics;
  memory_access: string[];
  status: 'active' | 'idle' | 'degraded' | 'offline';
  last_contribution: string | null;
  registered_at: string;
  extra_metadata: Record<string, any>;
}

// Mock data
const mockSources: IntelligenceSource[] = [
  {
    id: 'src-001',
    name: 'Work Laptop',
    type: 'endpoint',
    trust_score: 0.92,
    trust_level: 'HIGH',
    trust_history: [],
    contribution_metrics: {
      patterns_crystallized: 14,
      reasoning_steps_validated: 47,
      memory_matches_contributed: 102,
      decision_traces_triggered: 12,
      events_ingested: 543,
    },
    memory_access: ['gas', 'liquid', 'ice'],
    status: 'active',
    last_contribution: new Date().toISOString(),
    registered_at: new Date().toISOString(),
    extra_metadata: {},
  },
  {
    id: 'src-002',
    name: 'Factory Floor Sensor',
    type: 'iot',
    trust_score: 0.65,
    trust_level: 'BASIC',
    trust_history: [],
    contribution_metrics: {
      patterns_crystallized: 0,
      reasoning_steps_validated: 0,
      memory_matches_contributed: 0,
      decision_traces_triggered: 2,
      events_ingested: 1234,
    },
    memory_access: ['gas'],
    status: 'active',
    last_contribution: new Date().toISOString(),
    registered_at: new Date().toISOString(),
    extra_metadata: {},
  },
];

// Helper Functions
const formatTimeAgo = (timestamp: string | null): string => {
  if (!timestamp) return 'Never';
  const date = new Date(timestamp);
  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSeconds < 60) return 'Just now';
  if (diffSeconds < 3600) return `${Math.floor(diffSeconds / 60)}m ago`;
  if (diffSeconds < 86400) return `${Math.floor(diffSeconds / 3600)}h ago`;
  return `${Math.floor(diffSeconds / 86400)}d ago`;
};

const getTrustLevelClass = (level: string): string => {
  const map: Record<string, string> = {
    FULL: 'badgeFull',
    HIGH: 'badgeHigh',
    MEDIUM: 'badgeMedium',
    BASIC: 'badgeBasic',
    UNTRUSTED: 'badgeUntrusted',
  };
  return map[level] || 'badge';
};

const getTypeClass = (type: string): string => {
  const map: Record<string, string> = {
    endpoint: 'badgeEndpoint',
    iot: 'badgeIot',
    agent: 'badgeAgent',
    behavior_pack: 'badgeBehaviorPack',
  };
  return map[type] || 'badge';
};

const getStatusClass = (status: string): string => {
  const map: Record<string, string> = {
    active: 'badgeActive',
    idle: 'badgeIdle',
    degraded: 'badgeDegraded',
    offline: 'badgeOffline',
  };
  return map[status] || 'badge';
};

export default function IntelligenceSourceControl() {
  const [sources] = useState<IntelligenceSource[]>(mockSources);
  const [selectedSourceId, setSelectedSourceId] = useState<string | null>(null);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const selectedSource = sources.find(s => s.id === selectedSourceId);

  // Stats
  const activeCount = sources.filter(s => s.status === 'active').length;
  const avgTrust = sources.reduce((sum, s) => sum + s.trust_score, 0) / (sources.length || 1);
  const totalContributions = sources.reduce(
    (sum, s) => sum + s.contribution_metrics.patterns_crystallized + s.contribution_metrics.reasoning_steps_validated,
    0
  );

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1>🧠 Intelligence Source Control</h1>
          <div className={styles.subtitle}>Manage and monitor all sources contributing to your sovereign intelligence network</div>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.btnSecondary} onClick={() => window.location.reload()}>🔄 Refresh</button>
          <button className={styles.btnPrimary} onClick={() => setShowRegisterModal(true)}>➕ Register Source</button>
        </div>
      </div>

      <div className={styles.statsBar}>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Active Sources</div>
          <div className={styles.statValue}>{activeCount}</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Average Trust Score</div>
          <div className={styles.statValue}>{(avgTrust * 100).toFixed(0)}%</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Total Contributions</div>
          <div className={styles.statValue}>{totalContributions.toLocaleString()}</div>
        </div>
        <div className={styles.statCard}>
          <div className={styles.statLabel}>Total Sources</div>
          <div className={styles.statValue}>{sources.length}</div>
        </div>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Source</th>
              <th>Type</th>
              <th>Trust Score</th>
              <th>Level</th>
              <th>Memory Access</th>
              <th>Contributions</th>
              <th>Status</th>
              <th>Last Activity</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sources.map(source => (
              <tr key={source.id} className={selectedSourceId === source.id ? styles.selected : ''} onClick={() => { setSelectedSourceId(source.id); setShowDetailModal(true); }}>
                <td><span className={styles.sourceName}>{source.name}</span></td>
                <td><span className={`${styles.badge} ${styles[getTypeClass(source.type)]}`}>{source.type}</span></td>
                <td>
                  <div className={styles.trustScore}>
                    <div className={styles.scoreBar}><div className={styles.fill} style={{ width: `${source.trust_score * 100}%`, background: source.trust_score >= 0.8 ? '#00b894' : source.trust_score >= 0.6 ? '#fdcb6e' : '#e17055' }} /></div>
                    <span className={styles.scoreText}>{(source.trust_score * 100).toFixed(0)}%</span>
                  </div>
                </td>
                <td><span className={`${styles.badge} ${styles[getTrustLevelClass(source.trust_level)]}`}>{source.trust_level}</span></td>
                <td>
                  {source.memory_access.map(layer => (
                    <span key={layer} className={`${styles.tag} ${styles[`tag${layer.charAt(0).toUpperCase() + layer.slice(1)}`] || ''}`}>{layer}</span>
                  ))}
                </td>
                <td>🧩 {source.contribution_metrics.patterns_crystallized} 🧠 {source.contribution_metrics.reasoning_steps_validated}</td>
                <td><span className={`${styles.badge} ${styles[getStatusClass(source.status)]}`}>{source.status}</span></td>
                <td style={{ fontSize: '12px', color: '#b2bec3' }}>{formatTimeAgo(source.last_contribution)}</td>
                <td><div className={styles.actionsCell}><button className={styles.iconButton} onClick={(e) => { e.stopPropagation(); setSelectedSourceId(source.id); setShowDetailModal(true); }} title="View">👁️</button></div></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showDetailModal && selectedSource && (
        <div className={`${styles.modalOverlay} ${styles.active}`} onClick={(e) => { if (e.target === e.currentTarget) setShowDetailModal(false); }}>
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h2>📊 {selectedSource.name}</h2>
              <button className={styles.modalClose} onClick={() => setShowDetailModal(false)}>✕</button>
            </div>
            <div className={styles.modalBody}>
              <div className={styles.formRow}>
                <div><div style={{ fontSize: '11px', color: '#b2bec3' }}>ID</div><div>{selectedSource.id}</div></div>
                <div><div style={{ fontSize: '11px', color: '#b2bec3' }}>Type</div><div>{selectedSource.type}</div></div>
              </div>
            </div>
            <div className={styles.modalFooter}><button className={styles.btnSecondary} onClick={() => setShowDetailModal(false)}>Close</button></div>
          </div>
        </div>
      )}
    </div>
  );
}
