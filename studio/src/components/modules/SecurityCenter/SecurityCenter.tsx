import React from 'react';
import { Shield, Lock, EyeOff, Globe, Server, UserCheck, ShieldCheck } from 'lucide-react';

const SecurityCenter: React.FC = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={20} color="var(--color-error)" /> Enterprise Security & Hardening
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <SecuritySection title="Identity & Access" icon={<UserCheck size={18} />}>
              <ConfigToggle label="SSO Integration (OIDC/SAML)" active />
              <ConfigToggle label="Multi-Factor Authentication (MFA)" active />
              <ConfigToggle label="Biometric Hardware Lock" active={false} />
              <ConfigToggle label="Just-In-Time (JIT) Provisioning" active />
            </SecuritySection>

            <SecuritySection title="Data Privacy" icon={<EyeOff size={18} />}>
              <ConfigToggle label="Auto-Redact PII/PHI" active />
              <ConfigToggle label="Field-Level Encryption" active />
              <ConfigToggle label="Differential Privacy" active={false} />
              <ConfigToggle label="Zero-Knowledge Proofs" active />
            </SecuritySection>
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
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Network Hardening</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
              <StatusCard icon={<Globe size={16} />} label="Inbound TLS 1.3" status="Secure" />
              <StatusCard icon={<Server size={16} />} label="mTLS Internal" status="Active" />
              <StatusCard icon={<Lock size={16} />} label="HSTS Policies" status="Enforced" />
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px' }}>Compliance Status</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <ComplianceItem label="SOC2 Type II" status="Compliant" />
              <ComplianceItem label="HIPAA (PHI)" status="Compliant" />
              <ComplianceItem label="GDPR (Right to Forget)" status="Compliant" />
              <ComplianceItem label="FEDRAMP" status="In Review" warning />
            </div>
          </div>

          <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.05)', padding: '24px', borderRadius: '16px', border: '1px solid rgba(239, 68, 68, 0.1)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-error)', margin: 0, fontWeight: 700 }}>Security Level</h3>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>Tier 4</div>
            <p style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              Maximum protection enabled. All data is encrypted at rest and in transit with local key ownership.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const SecuritySection: React.FC<{ title: string, icon: React.ReactNode, children: React.ReactNode }> = ({ title, icon, children }) => (
  <div style={{ 
    backgroundColor: 'var(--color-bg-secondary)', 
    padding: '24px', 
    borderRadius: '16px', 
    border: '1px solid var(--glass-border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px'
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-text-primary)', fontWeight: 600 }}>
      {icon} {title}
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {children}
    </div>
  </div>
);

const ConfigToggle: React.FC<{ label: string, active: boolean }> = ({ label, active }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{label}</span>
    <div style={{ 
      width: '32px', 
      height: '18px', 
      borderRadius: '9px', 
      backgroundColor: active ? 'var(--color-success)' : 'var(--color-bg-tertiary)',
      position: 'relative',
      cursor: 'pointer',
      border: '1px solid var(--glass-border)'
    }}>
      <div style={{ 
        width: '12px', 
        height: '12px', 
        borderRadius: '50%', 
        backgroundColor: 'white', 
        position: 'absolute',
        top: '2px',
        left: active ? '17px' : '2px',
        transition: 'left 0.2s ease'
      }} />
    </div>
  </div>
);

const StatusCard: React.FC<{ icon: React.ReactNode, label: string, status: string }> = ({ icon, label, status }) => (
  <div style={{ backgroundColor: 'var(--color-bg-tertiary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '10px' }}>
    <div style={{ color: 'var(--color-success)' }}>{icon}</div>
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>{status}</div>
    </div>
  </div>
);

const ComplianceItem: React.FC<{ label: string, status: string, warning?: boolean }> = ({ label, status, warning }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{label}</span>
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      {warning ? null : <ShieldCheck size={12} color="var(--color-success)" />}
      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: warning ? 'var(--color-warning)' : 'var(--color-success)' }}>{status}</span>
    </div>
  </div>
);

export default SecurityCenter;
