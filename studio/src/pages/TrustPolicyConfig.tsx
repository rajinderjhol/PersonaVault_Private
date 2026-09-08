/**
 * Trust Policy Configuration Page
 * V2 Studio - CSS Modules version (No Chakra UI)
 */

import React, { useState } from 'react';
import styles from '../components/modules/TrustPolicyConfig/TrustPolicyConfig.module.css';

// Types
interface TrustPolicy {
  id: string;
  layer: string;
  min_trust_threshold: number;
  max_trust_threshold: number | null;
  is_enforced: boolean;
  action_on_violation: string;
  notification_enabled: boolean;
  created_at: string;
  updated_at: string;
}

// Mock data
const mockPolicies: TrustPolicy[] = [
  {
    id: 'pol-001',
    layer: 'gas',
    min_trust_threshold: 0.30,
    max_trust_threshold: null,
    is_enforced: true,
    action_on_violation: 'warn',
    notification_enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'pol-002',
    layer: 'liquid',
    min_trust_threshold: 0.50,
    max_trust_threshold: null,
    is_enforced: true,
    action_on_violation: 'block',
    notification_enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'pol-003',
    layer: 'ice',
    min_trust_threshold: 0.70,
    max_trust_threshold: null,
    is_enforced: true,
    action_on_violation: 'block',
    notification_enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'pol-004',
    layer: 'crystallized',
    min_trust_threshold: 0.85,
    max_trust_threshold: null,
    is_enforced: true,
    action_on_violation: 'block',
    notification_enabled: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const LAYER_LABELS: Record<string, string> = {
  gas: 'Gas (Working Memory)',
  liquid: 'Liquid (Episodic Memory)',
  ice: 'Ice (Semantic Memory)',
  crystallized: 'Crystallized (Patterns)',
};

const LAYER_COLORS: Record<string, string> = {
  gas: 'gas',
  liquid: 'liquid',
  ice: 'ice',
  crystallized: 'crystallized',
};

const getTrustColor = (score: number): string => {
  if (score >= 0.8) return 'green';
  if (score >= 0.6) return 'yellow';
  return 'red';
};

export default function TrustPolicyConfig() {
  const [policies] = useState<TrustPolicy[]>(mockPolicies);
  const [showSimulationModal, setShowSimulationModal] = useState(false);

  const policyMap = policies.reduce((acc, p) => {
    acc[p.layer] = p;
    return acc;
  }, {} as Record<string, TrustPolicy>);

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1>🛡️ Trust Policy Configuration</h1>
          <div className={styles.subtitle}>
            Configure memory layer access thresholds — the Decision Firewall for your intelligence sources
          </div>
        </div>
        <div className={styles.headerActions}>
          <button className={styles.btnSecondary} onClick={() => window.location.reload()}>
            🔄 Refresh
          </button>
          <button className={styles.btnPrimary}>
            🧪 Simulate Impact
          </button>
        </div>
      </div>

      {/* Alert */}
      <div className={`${styles.alert} ${styles.alertInfo}`}>
        <span className={styles.alertIcon}>ℹ️</span>
        <div className={styles.alertContent}>
          <div className={styles.alertTitle}>Decision Firewall Active</div>
          <div className={styles.alertDescription}>
            Trust policies define the minimum trust score required for a source to write to each memory layer.
            When a source's trust score falls below the threshold, the configured action is triggered.
          </div>
        </div>
      </div>

      {/* Policy Cards */}
      <div className={styles.policyGrid}>
        {Object.entries(LAYER_LABELS).map(([layer, label]) => {
          const policy = policyMap[layer];
          const threshold = policy ? policy.min_trust_threshold * 100 : 40;
          const isEnforced = policy ? policy.is_enforced : true;
          const action = policy ? policy.action_on_violation : 'block';

          return (
            <div key={layer} className={styles.policyCard}>
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  <span className={`${styles.layerBadge} ${styles[LAYER_COLORS[layer]]}`}>
                    {layer.toUpperCase()}
                  </span>
                  <span style={{ fontWeight: 500 }}>{label}</span>
                </div>
                <span className={`${styles.enforcementBadge} ${isEnforced ? styles.enforced : styles.notEnforced}`}>
                  {isEnforced ? '🔒 Enforced' : '🔓 Not Enforced'}
                </span>
              </div>
              <div className={styles.cardBody}>
                {/* Slider */}
                <div className={styles.sliderGroup}>
                  <div className={styles.sliderHeader}>
                    <span className={styles.sliderLabel}>Minimum Trust Threshold</span>
                    <span className={`${styles.sliderValue} ${styles[getTrustColor(threshold / 100)]}`}>
                      {Math.round(threshold)}%
                    </span>
                  </div>
                  <div className={styles.sliderTrack}>
                    <div
                      className={`${styles.sliderFill} ${styles[getTrustColor(threshold / 100)]}`}
                      style={{ width: `${threshold}%` }}
                    />
                    <div
                      className={styles.sliderThumb}
                      style={{ left: `${threshold}%` }}
                    />
                  </div>
                  <div className={styles.sliderLabels}>
                    <span>0% (Allow All)</span>
                    <span>100% (Strict)</span>
                  </div>
                </div>

                {/* Toggle Row */}
                <div className={styles.toggleRow}>
                  <span className={styles.toggleLabel}>Enforce Policy</span>
                  <div className={`${styles.toggleSwitch} ${isEnforced ? styles.active : ''}`}>
                    <div className={styles.toggleKnob} />
                  </div>
                </div>

                {/* Action Select */}
                <div className={styles.toggleRow}>
                  <span className={styles.toggleLabel}>On Violation</span>
                  <select className={styles.selectSm} defaultValue={action}>
                    <option value="block">🚫 Block</option>
                    <option value="warn">⚠️ Warn</option>
                    <option value="quarantine">📦 Quarantine</option>
                  </select>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Simulation Card */}
      <div className={styles.simulationCard}>
        <div className={styles.simulationRow}>
          <span className={styles.simulationLabel}>Test Policy Impact On:</span>
          <select className={styles.simulationSelect}>
            <option value="">Select a source...</option>
            <option value="src-001">Work Laptop (92% trust)</option>
            <option value="src-002">Factory Floor Sensor (65% trust)</option>
          </select>
          <span className={styles.simulationHint}>
            Select a source to test policy enforcement
          </span>
          <button className={styles.btnPrimary} style={{ marginLeft: 'auto' }}>
            🧪 Simulate Impact
          </button>
        </div>
      </div>
    </div>
  );
}
