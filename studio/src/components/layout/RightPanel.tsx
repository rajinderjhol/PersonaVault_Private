import React from 'react';
import { Thermometer, BrainCircuit, History } from 'lucide-react';
import { useTraceStore } from '../../store/traceStore';
import { useAuthStore } from '../../store/authStore';
import { useThermodynamicsQuery } from '../../hooks/query/useThermodynamicsQuery';
import { motion } from 'framer-motion';
import styles from './RightPanel.module.css';

const RightPanel: React.FC = () => {
  const { activeTrace } = useTraceStore();
  const { isAuthenticated } = useAuthStore();
  
  const { data, isLoading } = useThermodynamicsQuery();
  const { phases, transitions } = data || { phases: null, transitions: [] };

  if (isLoading && !data) {
     return <div className={styles.loading}>Loading...</div>;
  }

  return (
    <aside className={`${styles.container}`}>
      {/* Memory Phases */}
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>
          <Thermometer size={16} /> Memory Phases
        </h3>
        {phases ? (
          <div className={styles.list}>
            <PhaseItem label="Gas (Working)" color="var(--color-gas)" percentage={phases.gas} total={phases.total} />
            <PhaseItem label="Liquid (Episodic)" color="var(--color-liquid)" percentage={phases.liquid} total={phases.total} />
            <PhaseItem label="Ice (Semantic)" color="var(--color-ice)" percentage={phases.ice} total={phases.total} />
            <PhaseItem label="Snowflakes (Domain)" color="var(--color-text-primary)" percentage={phases.snowflakes} total={phases.total} />
          </div>
        ) : (
          <div className={styles.description}>Loading phases...</div>
        )}
      </div>

      {/* Active Decision Trace */}
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>
          <BrainCircuit size={16} /> Active Decision Trace
        </h3>
        {activeTrace ? (
          <div className={styles.traceSteps}>
            {activeTrace.steps.map((step) => (
              <TraceStep 
                key={step.id} 
                label={step.label} 
                status={step.status} 
              />
            ))}
          </div>
        ) : (
          <div className={styles.description}>
            No active trace.
          </div>
        )}
      </div>

      {/* Thermodynamic Transitions */}
      <div className={styles.card}>
        <h3 className={styles.cardTitle}>
          <History size={16} /> Phase Transitions
        </h3>
        <div className={styles.list}>
          {transitions.length > 0 ? transitions.map((log, i) => (
            <div key={i} className={styles.transitionItem}>
              {log.description}
            </div>
          )) : (
            <div className={styles.description}>No recent transitions</div>
          )}
        </div>
      </div>
    </aside>
  );
};

const PhaseItem: React.FC<{ label: string, color: string, percentage: number, total: number }> = ({ label, color, percentage, total }) => {
  const p = total > 0 ? (percentage / total) * 100 : 0;
  return (
    <div className={styles.listItem}>
      <div className={styles.phaseLabelRow}>
        <span>{label}</span>
        <span>{percentage}</span>
      </div>
      <div className={styles.progressBar}>
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${p}%` }}
          className={styles.progressFill}
          style={{ backgroundColor: color }} 
        />
      </div>
    </div>
  );
};

const TraceStep: React.FC<{ label: string, status: string }> = ({ label, status }) => (
  <div className={`${styles.traceStep} ${styles[status]}`}>
    <div className={styles.traceDot} />
    <span className={styles.traceLabel}>
      {label}
    </span>
  </div>
);

export default RightPanel;
