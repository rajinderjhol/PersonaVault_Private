import React, { useState, useEffect } from 'react';
import { useV2DecisionTrace } from '../../hooks/query/v2/useV2DecisionTrace';
import styles from './DecisionReplay.module.css';

interface DecisionReplayProps {
  decisionId: string;
}

export const DecisionReplay: React.FC<DecisionReplayProps> = ({ decisionId }) => {
  const { data: trace, isLoading } = useV2DecisionTrace(decisionId);
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let interval: any;
    if (isPlaying && trace) {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= trace.steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 2000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying, trace]);

  if (isLoading) return <div className={styles.loading}>Loading decision trace...</div>;
  if (!trace) return <div className={styles.error}>Decision trace not found</div>;

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleInfo}>
          <span className={styles.icon}>🎯</span>
          <span className={styles.title}>Decision Replay</span>
        </div>
        <div className={styles.controls}>
          <button 
            className={styles.controlBtn} 
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? '⏸️ Pause' : '▶️ Play'}
          </button>
          <button 
            className={styles.controlBtn} 
            onClick={() => { setIsPlaying(false); setCurrentStep(0); }}
          >
            ⏮️ Reset
          </button>
        </div>
      </div>
      
      <div className={styles.summary}>
        <strong>Verdict:</strong> {trace.verdict}
        <p>{trace.summary}</p>
      </div>
      
      <div className={styles.timeline}>
        {trace.steps.map((step, index) => (
          <div 
            key={index}
            className={`${styles.step} ${index <= currentStep ? styles.completed : ''} ${index === currentStep ? styles.active : ''}`}
            onClick={() => setCurrentStep(index)}
          >
            <div className={styles.stepIndicator}>
              {index < currentStep ? '✅' : index === currentStep ? '⏳' : '⏸️'}
            </div>
            <div className={styles.stepContent}>
              <div className={styles.stepHeader}>
                <span className={styles.stepLabel}>{step.label}</span>
                <span className={styles.stepTime}>{new Date(step.timestamp).toLocaleTimeString()}</span>
              </div>
              <div className={styles.stepDetails}>{step.details}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
