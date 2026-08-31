import React from 'react';
import { Thermometer, BrainCircuit, History } from 'lucide-react';
import { useTraceStore } from '../../store/traceStore';
import { useAuthStore } from '../../store/authStore';
import { useThermodynamicsQuery } from '../../hooks/query/useThermodynamicsQuery';
import { motion } from 'framer-motion';

const RightPanel: React.FC = () => {
  const { activeTrace } = useTraceStore();
  const { isAuthenticated } = useAuthStore();
  
  const { data, isLoading } = useThermodynamicsQuery();
  const { phases, transitions } = data || { phases: null, transitions: [] };

  if (isLoading && !data) {
     return <div>Loading...</div>;
  }

  return (
    <aside className="glass-panel" style={{
      width: 'var(--right-panel-width)',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px',
      gap: '24px',
      overflowY: 'auto',
      borderLeft: '1px solid var(--glass-border)',
      borderTop: 'none',
      borderBottom: 'none',
      borderRight: 'none'
    }}>
      {/* Memory Phases */}
      <div>
        <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Thermometer size={16} /> Memory Phases
        </h3>
        {phases ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <PhaseItem label="Gas (Working)" color="var(--color-gas)" percentage={phases.gas} total={phases.total} />
            <PhaseItem label="Liquid (Episodic)" color="var(--color-liquid)" percentage={phases.liquid} total={phases.total} />
            <PhaseItem label="Ice (Semantic)" color="var(--color-ice)" percentage={phases.ice} total={phases.total} />
            <PhaseItem label="Snowflakes (Domain)" color="var(--color-text-primary)" percentage={phases.snowflakes} total={phases.total} />
          </div>
        ) : (
          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>Loading phases...</div>
        )}
      </div>

      {/* Active Decision Trace */}
      <div style={{ flex: 1 }}>
        <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BrainCircuit size={16} /> Active Decision Trace
        </h3>
        {activeTrace ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0', position: 'relative', paddingLeft: '10px' }}>
            {activeTrace.steps.map((step, index) => (
              <TraceStep 
                key={step.id} 
                label={step.label} 
                status={step.status} 
                isLast={index === activeTrace.steps.length - 1} 
              />
            ))}
          </div>
        ) : (
          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem', textAlign: 'center', marginTop: '20px' }}>
            No active trace.
          </div>
        )}
      </div>

      {/* Thermodynamic Transitions */}
      <div>
        <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <History size={16} /> Phase Transitions
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {transitions.length > 0 ? transitions.map((log, i) => (
            <div key={i} style={{ 
              backgroundColor: 'var(--color-bg-tertiary)', 
              padding: '10px', 
              borderRadius: '8px', 
              fontSize: '0.75rem', 
              color: 'var(--color-text-secondary)', 
              border: '1px solid var(--glass-border)',
              fontFamily: 'monospace'
            }}>
              {log.description}
            </div>
          )) : (
            <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>No recent transitions</div>
          )}
        </div>
      </div>
    </aside>
  );
};

const PhaseItem: React.FC<{ label: string, color: string, percentage: number, total: number }> = ({ label, color, percentage, total }) => {
  const p = total > 0 ? (percentage / total) * 100 : 0;
  return (
    <div style={{ fontSize: '0.85rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
        <span>{label}</span>
        <span>{percentage}</span>
      </div>
      <div style={{ height: '4px', backgroundColor: 'var(--color-bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${p}%` }}
          style={{ height: '100%', backgroundColor: color }} 
        />
      </div>
    </div>
  );
};

const TraceStep: React.FC<{ label: string, status: string, isLast: boolean }> = ({ label, status, isLast }) => (
  <div style={{ 
    display: 'flex', 
    alignItems: 'center', 
    gap: '12px', 
    height: '40px',
    position: 'relative'
  }}>
    <div style={{ 
      width: '12px', 
      height: '12px', 
      borderRadius: '50%', 
      backgroundColor: status === 'complete' ? 'var(--color-success)' : status === 'active' ? 'var(--color-gas)' : 'var(--color-bg-tertiary)',
      border: status === 'active' ? '2px solid var(--color-gas)' : 'none',
      boxShadow: status === 'active' ? '0 0 10px var(--color-gas)' : 'none',
      zIndex: 2
    }} />
    <span style={{ 
      fontSize: '0.85rem', 
      color: status === 'complete' ? 'var(--color-text-primary)' : status === 'active' ? 'var(--color-gas)' : 'var(--color-text-muted)',
      fontWeight: status === 'active' ? 600 : 400
    }}>
      {label}
    </span>
    {/* Connector Line */}
    {!isLast && (
      <div style={{
        position: 'absolute',
        left: '5px',
        top: '20px',
        width: '2px',
        height: '40px',
        backgroundColor: 'var(--color-bg-tertiary)',
        zIndex: 1
      }} />
    )}
  </div>
);

export default RightPanel;
