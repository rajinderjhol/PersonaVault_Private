import React from 'react';
import { useGovernanceStore } from '../../../store/governanceStore';
import { Shield, Lock, Scale, RefreshCw, CheckCircle, AlertTriangle, FileText } from 'lucide-react';
import LegalHold from './LegalHold';

const Governance: React.FC = () => {
  const { constitution, veriLinkStatus, lastRotation, rotateKeys } = useGovernanceStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', height: '100%' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Scale size={20} color="var(--color-liquid)" /> Local Guardian Constitution
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {constitution.map(rule => (
              <RuleCard key={rule.id} rule={rule} />
            ))}
          </div>

          <LegalHold />

          <div style={{
            backgroundColor: 'var(--color-bg-secondary)',
            padding: '24px',
            borderRadius: '16px',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Compliance Export</h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0 }}>
              Generate a cryptographically signed report of all decisions, policies, and evidence traces for a specific timeframe.
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button style={{ flex: 1, backgroundColor: 'var(--color-bg-tertiary)', color: 'white', border: '1px solid var(--glass-border)', padding: '10px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <FileText size={16} /> JSON Report
              </button>
              <button style={{ flex: 1, backgroundColor: 'var(--color-bg-tertiary)', color: 'white', border: '1px solid var(--glass-border)', padding: '10px', borderRadius: '8px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                <FileText size={16} /> PDF Ledger
              </button>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* VeriLink Status */}
          <div style={{ 
            backgroundColor: veriLinkStatus === 'verified' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', 
            padding: '24px', 
            borderRadius: '16px', 
            border: `1px solid ${veriLinkStatus === 'verified' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'}`,
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: veriLinkStatus === 'verified' ? 'var(--color-success)' : 'var(--color-error)', margin: 0, fontWeight: 700 }}>
                VeriLink Status
              </h3>
              {veriLinkStatus === 'verified' ? <CheckCircle size={18} color="var(--color-success)" /> : <AlertTriangle size={18} color="var(--color-error)" />}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Integrity Verified</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-secondary)' }}>All decisions match cryptographic provenance receipts.</div>
            </div>
            <div style={{ borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>Last Key Rotation:</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-primary)', fontFamily: 'monospace' }}>{new Date(lastRotation).toLocaleString()}</div>
            </div>
            <button 
              onClick={rotateKeys}
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.05)',
                color: 'white',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                padding: '10px',
                borderRadius: '8px',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '8px'
              }}
            >
              <RefreshCw size={14} /> Rotate Trust Keys
            </button>
          </div>

          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px' }}>Policy Overview</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <OverviewItem label="Active Restrictions" value="14" color="var(--color-error)" />
              <OverviewItem label="Mandatory Obligations" value="6" color="var(--color-gas)" />
              <OverviewItem label="Pending Reviews" value="2" color="var(--color-warning)" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const RuleCard: React.FC<{ rule: any }> = ({ rule }) => {
  const isRestriction = rule.type === 'restriction';
  
  return (
    <div style={{ 
      backgroundColor: 'var(--color-bg-secondary)', 
      padding: '20px', 
      borderRadius: '12px', 
      border: '1px solid var(--glass-border)',
      display: 'flex',
      gap: '16px',
      alignItems: 'flex-start',
      transition: 'all 0.2s ease'
    }}>
      <div style={{ 
        width: '40px', 
        height: '40px', 
        borderRadius: '10px', 
        backgroundColor: isRestriction ? 'rgba(239, 68, 68, 0.1)' : 'rgba(14, 165, 233, 0.1)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        color: isRestriction ? 'var(--color-error)' : 'var(--color-accent)',
        flexShrink: 0
      }}>
        {isRestriction ? <Lock size={20} /> : <Shield size={20} />}
      </div>
      
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '1rem' }}>{rule.name}</div>
          <div style={{ 
            fontSize: '0.65rem', 
            padding: '2px 8px', 
            borderRadius: '10px', 
            backgroundColor: rule.status === 'active' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            color: rule.status === 'active' ? 'var(--color-success)' : 'var(--color-warning)',
            textTransform: 'uppercase',
            fontWeight: 700
          }}>
            {rule.status}
          </div>
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{rule.description}</div>
      </div>
    </div>
  );
};

const OverviewItem: React.FC<{ label: string, value: string, color: string }> = ({ label, value, color }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{label}</span>
    <span style={{ fontSize: '1rem', fontWeight: 700, color: color }}>{value}</span>
  </div>
);

export default Governance;
