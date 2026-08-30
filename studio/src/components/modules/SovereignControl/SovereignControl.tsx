import React from 'react';
import { useSovereignStore } from '../../../store/sovereignStore';
import type { ExecutionMode } from '../../../store/sovereignStore';
import { Shield, Zap, Search, Eye, WifiOff, Globe, Server, Database, Info } from 'lucide-react';

const SovereignControl: React.FC = () => {
  const { executionMode, airGapped, dataSovereigntyLevel, setMode, toggleAirGapped, setSovereignty } = useSovereignStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={20} color="var(--color-liquid)" /> Sovereign Execution Control
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <ModeCard 
              mode="standard" 
              active={executionMode === 'standard'} 
              icon={<Zap size={24} />} 
              label="Standard Mode"
              description="Full tool access with mandatory human-in-the-loop gates for high-risk actions."
              onClick={() => setMode('standard')}
              color="var(--color-gas)"
            />
            <ModeCard 
              mode="restricted" 
              active={executionMode === 'restricted'} 
              icon={<WifiOff size={24} />} 
              label="Restricted Mode"
              description="Air-gapped execution utilizing only crystallized 'Ice' semantic memory."
              onClick={() => setMode('restricted')}
              color="var(--color-error)"
            />
            <ModeCard 
              mode="simulation" 
              active={executionMode === 'simulation'} 
              icon={<Search size={24} />} 
              label="Simulation Mode"
              description="Sandboxed decision replay with no side effects. Used for policy validation."
              onClick={() => setMode('simulation')}
              color="var(--color-liquid)"
            />
            <ModeCard 
              mode="audit" 
              active={executionMode === 'audit'} 
              icon={<Eye size={24} />} 
              label="Audit Mode"
              description="Read-only access with intensified system logging and provenance tracking."
              onClick={() => setMode('audit')}
              color="var(--color-ice)"
            />
          </div>

          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px'
          }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Physical Data Sovereignty</h3>
            <div style={{ display: 'flex', gap: '12px' }}>
              <SovereigntyOption 
                active={dataSovereigntyLevel === 'local'} 
                icon={<Server size={18} />} 
                label="On-Premise (Local)" 
                onClick={() => setSovereignty('local')}
              />
              <SovereigntyOption 
                active={dataSovereigntyLevel === 'hybrid'} 
                icon={<Database size={18} />} 
                label="Sovereign Cloud" 
                onClick={() => setSovereignty('hybrid')}
              />
              <SovereigntyOption 
                active={dataSovereigntyLevel === 'cloud'} 
                icon={<Globe size={18} />} 
                label="Global Cloud" 
                onClick={() => setSovereignty('cloud')}
              />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Air-Gapped Status */}
          <div style={{ 
            backgroundColor: airGapped ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)', 
            padding: '24px', 
            borderRadius: '16px', 
            border: `1px solid ${airGapped ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: airGapped ? 'var(--color-error)' : 'var(--color-success)', margin: 0, fontWeight: 700 }}>
                {airGapped ? 'Isolated' : 'Connected'}
              </h3>
              {airGapped ? <WifiOff size={18} color="var(--color-error)" /> : <Globe size={18} color="var(--color-success)" />}
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              {airGapped 
                ? 'External model providers (Groq, Gemini) are disabled. Running on local Ollama instances only.' 
                : 'System is connected to external inference engines and cloud memory sync.'}
            </p>
            <button 
              onClick={toggleAirGapped}
              style={{
                backgroundColor: airGapped ? 'var(--color-error)' : 'var(--color-bg-tertiary)',
                color: 'white',
                border: 'none',
                padding: '12px',
                borderRadius: '8px',
                fontSize: '0.9rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease'
              }}
            >
              {airGapped ? 'Disable Isolation' : 'Enable Air-Gapped Mode'}
            </button>
          </div>

          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px' }}>Security Audit</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', display: 'flex', gap: '8px' }}>
                <Info size={14} color="var(--color-gas)" />
                Last key rotation: 2h ago
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', display: 'flex', gap: '8px' }}>
                <Info size={14} color="var(--color-gas)" />
                VeriLink Status: Verified
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const ModeCard: React.FC<{ mode: ExecutionMode, active: boolean, icon: React.ReactNode, label: string, description: string, onClick: () => void, color: string }> = ({ active, icon, label, description, onClick, color }) => (
  <div 
    onClick={onClick}
    style={{
      backgroundColor: active ? 'var(--color-bg-tertiary)' : 'var(--color-bg-secondary)',
      padding: '24px',
      borderRadius: '16px',
      border: `1px solid ${active ? color : 'var(--glass-border)'}`,
      cursor: 'pointer',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      transition: 'all 0.2s ease',
      boxShadow: active ? `0 0 15px ${color}22` : 'none'
    }}
  >
    <div style={{ color: active ? color : 'var(--color-text-muted)', transition: 'all 0.2s ease' }}>{icon}</div>
    <div style={{ fontWeight: 600, fontSize: '1.1rem', color: active ? 'var(--color-text-primary)' : 'var(--color-text-secondary)' }}>{label}</div>
    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', lineHeight: 1.4 }}>{description}</div>
  </div>
);

const SovereigntyOption: React.FC<{ active: boolean, icon: React.ReactNode, label: string, onClick: () => void }> = ({ active, icon, label, onClick }) => (
  <div 
    onClick={onClick}
    style={{
      flex: 1,
      backgroundColor: active ? 'var(--color-liquid)' : 'var(--color-bg-tertiary)',
      color: active ? 'white' : 'var(--color-text-secondary)',
      padding: '12px',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '10px',
      cursor: 'pointer',
      fontSize: '0.85rem',
      fontWeight: 600,
      border: '1px solid var(--glass-border)',
      transition: 'all 0.2s ease'
    }}
  >
    {icon} {label}
  </div>
);

export default SovereignControl;
