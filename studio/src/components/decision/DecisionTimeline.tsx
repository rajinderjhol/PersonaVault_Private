import React from 'react';
import styles from './DecisionTimeline.module.css';

interface Props {
  timeline: {
    perception: any;
    policyMatch: any;
    aiRecommendation: any;
    decisionMade: any;
    provenanceLogged: any;
  };
}

const TIMELINE_STEPS: Array<{ key: keyof Props['timeline']; icon: string; label: string }> = [
  { key: 'perception', icon: '🔍', label: 'Perception' },
  { key: 'policyMatch', icon: '📋', label: 'Policy Match' },
  { key: 'aiRecommendation', icon: '🤖', label: 'AI Recommendation' },
  { key: 'decisionMade', icon: '👤', label: 'Decision Made' },
  { key: 'provenanceLogged', icon: '🔒', label: 'Provenance Logged' },
];

export const DecisionTimeline: React.FC<Props> = ({ timeline }) => {
  return (
    <div className={styles.container}>
      {TIMELINE_STEPS.map((step, index) => (
        <div key={step.key} className={styles.step}>
          <div className={styles.stepHeader}>
            <span className={styles.stepIcon}>{step.icon}</span>
            <span className={styles.stepLabel}>{step.label}</span>
            <span className={styles.stepNumber}>Step {index + 1}</span>
          </div>
          <div className={styles.stepContent}>
            <pre className={styles.stepDetails}>
              {JSON.stringify(timeline[step.key], null, 2)}
            </pre>
          </div>
          {index < TIMELINE_STEPS.length - 1 && (
            <div className={styles.stepConnector} />
          )}
        </div>
      ))}
    </div>
  );
};
