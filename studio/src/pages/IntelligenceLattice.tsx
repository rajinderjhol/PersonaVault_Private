import React, { useState } from 'react';
import { useV2Lattice, useV2LatticeHistory } from '../hooks/query/v2/useV2Lattice';
import styles from './IntelligenceLattice.module.css';

export const IntelligenceLattice: React.FC = () => {
  const { data: lattice, isLoading, error } = useV2Lattice();
  const { data: history } = useV2LatticeHistory();

  if (isLoading) {
    return (
      <div className={styles.loadingContainer}>
        <div className={styles.loadingSpinner} />
        <p>Loading Intelligence Lattice...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={styles.errorContainer}>
        <span className={styles.errorIcon}>⚠️</span>
        <h3>Failed to load lattice data</h3>
        <p>{error.message}</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🧊 Intelligence Lattice</h1>
        <p>Visualize memory phases and intelligence accumulation</p>
        <div className={styles.statsBar}>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Total Memories</span>
            <span className={styles.statValue}>{lattice?.total || 0}</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Crystallization Rate</span>
            <span className={styles.statValue}>{lattice?.crystallizationRate || 0}%</span>
          </div>
          <div className={styles.stat}>
            <span className={styles.statLabel}>Compression Ratio</span>
            <span className={styles.statValue}>{lattice?.compressionRatio || 0}:1</span>
          </div>
        </div>
      </div>

      {/* Phase Visualization */}
      <div className={styles.phaseSection}>
        <h2>📊 Memory Phases</h2>
        <div className={styles.phaseGrid}>
          {lattice?.phases.map((phase) => (
            <div key={phase.name} className={styles.phaseCard}>
              <div className={styles.phaseHeader}>
                <span className={styles.phaseIcon} style={{ color: phase.color }}>
                  {phase.name === 'Gas' ? '💨' : 
                   phase.name === 'Liquid' ? '💧' : 
                   phase.name === 'Ice' ? '🧊' : '❄️'}
                </span>
                <span className={styles.phaseName}>{phase.name}</span>
                <span className={styles.phaseCount}>{phase.count}</span>
              </div>
              <div className={styles.phaseBar}>
                <div 
                  className={styles.phaseFill}
                  style={{ 
                    width: `${phase.percentage}%`,
                    backgroundColor: phase.color 
                  }}
                />
              </div>
              <div className={styles.phasePercentage}>{phase.percentage}%</div>
              <div className={styles.phaseDescription}>{phase.description}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Phase Transitions */}
      {lattice?.transitions && lattice.transitions.length > 0 && (
        <div className={styles.transitionsSection}>
          <h2>🔄 Recent Transitions</h2>
          <div className={styles.transitionsList}>
            {lattice.transitions.map((transition, index) => (
              <div key={index} className={styles.transitionItem}>
                <span className={styles.transitionArrow}>
                  {transition.from} → {transition.to}
                </span>
                <span className={styles.transitionCount}>{transition.count} events</span>
                <span className={styles.transitionTime}>
                  {new Date(transition.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Growth Chart */}
      {history && history.length > 0 && (
        <div className={styles.growthSection}>
          <h2>📈 Intelligence Growth</h2>
          <div className={styles.chartContainer}>
            <div className={styles.chart}>
              {history.map((dataPoint, index) => {
                const maxValue = Math.max(...history.map(h => h.total));
                const height = maxValue > 0 ? (dataPoint.total / maxValue) * 200 : 0;
                return (
                  <div key={index} className={styles.barContainer}>
                    <div 
                      className={styles.bar}
                      style={{ height: `${height}px` }}
                      title={`${dataPoint.total} memories`}
                    />
                    <div className={styles.barLabel}>
                      {new Date(dataPoint.growth[0]?.date || '').toLocaleDateString()}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
