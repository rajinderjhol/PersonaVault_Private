import React from 'react';
import { motion } from 'framer-motion';
import { 
  Search, 
  ShieldCheck, 
  BrainCircuit, 
  Fingerprint, 
  Lock,
  ArrowRight,
  Database,
  Cpu
} from 'lucide-react';

interface StoryboardStep {
  id: string;
  type: 'perception' | 'policy' | 'swarm' | 'decision' | 'provenance';
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  data?: any;
}

interface DecisionTraceStoryboardProps {
  trace: any;
  onClose?: () => void;
}

export const DecisionTraceStoryboard: React.FC<DecisionTraceStoryboardProps> = ({ 
  trace, 
  onClose 
}) => {
  if (!trace) return null;

  // Map trace data to storyboard steps
  const steps: StoryboardStep[] = [
    {
      id: 'step-1',
      type: 'perception',
      label: 'Perception',
      description: 'The system identified the core intent and active context.',
      icon: <Search size={18} />,
      color: 'var(--color-gas, #00f2ff)',
      data: trace.perception
    },
    {
      id: 'step-2',
      type: 'policy',
      label: 'Governance Match',
      description: 'Intelligence packs and safety policies were applied.',
      icon: <ShieldCheck size={18} />,
      color: 'var(--color-liquid, #ffd93d)',
      data: trace.policy_match
    },
    {
      id: 'step-3',
      type: 'swarm',
      label: 'Swarm Synthesis',
      description: 'Specialized agents collaborated to generate a recommendation.',
      icon: <BrainCircuit size={18} />,
      color: 'var(--color-ice, #4d96ff)',
      data: trace.ai_recommendation
    },
    {
      id: 'step-4',
      type: 'decision',
      label: 'Decision Commit',
      description: 'The system finalized the action based on swarm consensus.',
      icon: <Fingerprint size={18} />,
      color: 'var(--color-accent, #38bdf8)',
      data: trace.decision
    },
    {
      id: 'step-5',
      type: 'provenance',
      label: 'Provenance Rooted',
      description: 'The decision was logged into the sovereign audit lattice.',
      icon: <Lock size={18} />,
      color: '#6bcb77',
      data: trace.provenance
    }
  ];

  return (
    <div className="storyboard-container" style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      padding: '24px',
      backgroundColor: 'rgba(15, 23, 42, 0.4)',
      borderRadius: '16px',
      border: '1px solid var(--glass-border)',
      marginTop: '16px',
      backdropFilter: 'blur(10px)'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--color-text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Cpu size={20} color="var(--color-gas)" /> Cognitive Storyboard
        </h3>
        {onClose && (
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
            ✕
          </button>
        )}
      </div>

      <div className="steps-wrapper" style={{
        display: 'flex',
        justifyContent: 'space-between',
        position: 'relative'
      }}>
        {/* Connection Line */}
        <div style={{
          position: 'absolute',
          top: '20px',
          left: '40px',
          right: '40px',
          height: '2px',
          background: 'linear-gradient(90deg, var(--color-gas), var(--color-liquid), var(--color-ice), var(--color-accent), #6bcb77)',
          opacity: 0.2,
          zIndex: 0
        }} />

        {steps.map((step, index) => (
          <motion.div 
            key={step.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              width: '18%',
              zIndex: 1,
              textAlign: 'center'
            }}
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '12px',
              backgroundColor: 'rgba(15, 23, 42, 0.8)',
              border: `2px solid ${step.color}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: step.color,
              marginBottom: '12px',
              boxShadow: `0 0 15px ${step.color}33`
            }}>
              {step.icon}
            </div>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: step.color, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {step.label}
            </span>
          </motion.div>
        ))}
      </div>

      <div className="step-narrative" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginTop: '8px'
      }}>
        {steps.map((step, index) => (
          <div key={step.id} style={{
            padding: '12px',
            backgroundColor: 'rgba(15, 23, 42, 0.3)',
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.05)'
          }}>
            <p style={{ margin: '0 0 8px 0', fontSize: '0.8rem', color: 'var(--color-text-primary)', fontWeight: 600 }}>
              {step.label}
            </p>
            <p style={{ margin: 0, fontSize: '0.7rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>
              {step.description}
            </p>
            {step.data && (
              <div style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                {step.type === 'swarm' && step.data.provider && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.65rem', color: step.color }}>
                    <Database size={10} /> {step.data.provider} / {step.data.model}
                  </div>
                )}
                {step.type === 'policy' && step.data.matched && (
                  <div style={{ fontSize: '0.65rem', color: step.color }}>
                    Matched: {step.data.matched}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px', 
        fontSize: '0.7rem', 
        color: 'var(--color-text-muted)',
        marginTop: '8px',
        fontStyle: 'italic'
      }}>
        <ShieldCheck size={14} color="#6bcb77" /> 
        Provenance verified on sovereign lattice at {new Date(trace.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};
