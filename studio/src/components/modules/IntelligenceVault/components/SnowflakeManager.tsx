import React from 'react';
import { ArrowRight, Shield, Heart, Zap } from 'lucide-react';

const SnowflakeManager: React.FC = () => {
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
        Snowflake (Domain) Variants
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <SnowflakeItem icon={<Shield size={16} />} name="Security Ops" patterns={42} status="Active" />
        <SnowflakeItem icon={<Heart size={16} />} name="Health & Wellness" patterns={12} status="Hibernating" />
        <SnowflakeItem icon={<Zap size={16} />} name="Quick Response" patterns={8} status="Active" />
      </div>

      <div style={{
        marginTop: '10px',
        padding: '16px',
        borderRadius: '12px',
        background: 'linear-gradient(135deg, rgba(0, 242, 255, 0.05) 0%, transparent 100%)',
        border: '1px solid rgba(0, 242, 255, 0.1)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          Branch new domain variant from existing ice patterns?
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input 
            type="text" 
            placeholder="New Domain Name..." 
            style={{ 
              flex: 1, 
              backgroundColor: 'var(--color-bg-primary)', 
              border: '1px solid var(--glass-border)', 
              borderRadius: '6px', 
              padding: '8px 12px',
              fontSize: '0.85rem',
              color: 'var(--color-text-primary)',
              outline: 'none'
            }} 
          />
          <button style={{
            backgroundColor: 'var(--color-gas)',
            color: 'var(--color-bg-primary)',
            border: 'none',
            borderRadius: '6px',
            padding: '8px',
            cursor: 'pointer'
          }}>
            <ArrowRight size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

const SnowflakeItem: React.FC<{ icon: React.ReactNode, name: string, patterns: number, status: string }> = ({ icon, name, patterns, status }) => (
  <div style={{
    backgroundColor: 'var(--color-bg-tertiary)',
    padding: '12px 16px',
    borderRadius: '10px',
    border: '1px solid var(--glass-border)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center'
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
      <div style={{ color: 'var(--color-gas)' }}>{icon}</div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{name}</div>
        <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{patterns} Crystallized Patterns</div>
      </div>
    </div>
    <div style={{ 
      fontSize: '0.65rem', 
      padding: '2px 8px', 
      borderRadius: '10px', 
      backgroundColor: status === 'Active' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(100, 116, 139, 0.1)',
      color: status === 'Active' ? 'var(--color-success)' : 'var(--color-text-muted)',
      border: `1px solid ${status === 'Active' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)'}`
    }}>
      {status}
    </div>
  </div>
);

export default SnowflakeManager;
