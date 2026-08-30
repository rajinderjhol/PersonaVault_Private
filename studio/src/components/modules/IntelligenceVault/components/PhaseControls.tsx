import React from 'react';
import { useThermodynamicsStore } from '../../../../store/thermodynamicsStore';
import { Snowflake, Flame, Wind, Mountain, Plus } from 'lucide-react';

const PhaseControls: React.FC = () => {
  const { setPhase, addTransition, phases } = useThermodynamicsStore();

  const handleAction = (action: string, phase: 'gas' | 'liquid' | 'ice' | 'snowflake', delta: number) => {
    const currentValue = (phases as any)[phase];
    const newValue = Math.min(Math.max(currentValue + delta, 0), 100);
    setPhase(phase, newValue);
    addTransition(`${action}: Manual phase adjustment applied to ${phase.toUpperCase()}`);
  };

  return (
    <div style={{
      backgroundColor: 'var(--color-bg-secondary)',
      borderRadius: '16px',
      padding: '24px',
      border: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', margin: 0, letterSpacing: '0.05em' }}>
        Phase Transition Controls
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <ControlButton 
          icon={<Snowflake size={18} />} 
          label="Freeze" 
          description="Crystallize context"
          color="var(--color-ice)"
          onClick={() => handleAction('Freeze', 'ice', 5)}
        />
        <ControlButton 
          icon={<Flame size={18} />} 
          label="Melt" 
          description="Dissolve patterns"
          color="var(--color-liquid)"
          onClick={() => handleAction('Melt', 'liquid', 5)}
        />
        <ControlButton 
          icon={<Wind size={18} />} 
          label="Evaporate" 
          description="Remove detail"
          color="var(--color-gas)"
          onClick={() => handleAction('Evaporate', 'gas', -5)}
        />
        <ControlButton 
          icon={<Mountain size={18} />} 
          label="Sublimate" 
          description="Direct to gas"
          color="var(--color-gas)"
          onClick={() => handleAction('Sublimate', 'gas', 5)}
        />
      </div>

      <button style={{
        marginTop: '10px',
        backgroundColor: 'rgba(0, 242, 255, 0.1)',
        border: '1px dashed var(--color-gas)',
        color: 'var(--color-gas)',
        padding: '12px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '10px',
        cursor: 'pointer',
        fontSize: '0.9rem',
        fontWeight: 600
      }}>
        <Plus size={18} /> New Transition Rule
      </button>
    </div>
  );
};

const ControlButton: React.FC<{ icon: React.ReactNode, label: string, description: string, color: string, onClick: () => void }> = ({ icon, label, description, color, onClick }) => (
  <div 
    onClick={onClick}
    style={{
      backgroundColor: 'var(--color-bg-tertiary)',
      padding: '16px',
      borderRadius: '12px',
      border: '1px solid var(--glass-border)',
      cursor: 'pointer',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      transition: 'all 0.2s ease'
    }}
    onMouseEnter={(e) => e.currentTarget.style.borderColor = color}
    onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--glass-border)'}
  >
    <div style={{ color: color }}>{icon}</div>
    <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--color-text-primary)' }}>{label}</div>
    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-secondary)' }}>{description}</div>
  </div>
);

export default PhaseControls;
