import React, { useState } from 'react';
import { Key, ShieldCheck, PenTool, Check, AlertCircle } from 'lucide-react';

const PackSigning: React.FC = () => {
  const [isSigning, setIsSigning] = useState(false);
  const [isSigned, setIsSigned] = useState(false);

  const handleSign = () => {
    setIsSigning(true);
    setTimeout(() => {
      setIsSigning(false);
      setIsSigned(true);
    }, 2000);
  };

  return (
    <div style={{
      backgroundColor: 'var(--color-bg-secondary)',
      padding: '24px',
      borderRadius: '16px',
      border: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <ShieldCheck size={20} color="var(--color-gas)" />
        <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0 }}>Cryptographic Pack Signing</h3>
      </div>

      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', margin: 0, lineHeight: 1.5 }}>
        Ensure this behavior pack is verified for production deployment by signing it with your organization's private trust key.
      </p>

      <div style={{
        backgroundColor: 'var(--color-bg-tertiary)',
        padding: '16px',
        borderRadius: '12px',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
            <Key size={14} /> Active Trust Key: <span style={{ fontFamily: 'monospace', color: 'var(--color-gas)' }}>PV-ORG-824...</span>
          </div>
          {isSigned && <div style={{ fontSize: '0.7rem', color: 'var(--color-success)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={12} /> VERIFIED</div>}
        </div>

        <button 
          onClick={handleSign}
          disabled={isSigning || isSigned}
          style={{
            backgroundColor: isSigned ? 'rgba(16, 185, 129, 0.1)' : 'var(--color-gas)',
            color: isSigned ? 'var(--color-success)' : 'var(--color-bg-primary)',
            border: isSigned ? '1px solid var(--color-success)' : 'none',
            padding: '12px',
            borderRadius: '8px',
            fontSize: '0.9rem',
            fontWeight: 700,
            cursor: isSigned ? 'default' : 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            transition: 'all 0.2s ease',
            opacity: isSigning ? 0.7 : 1
          }}
        >
          {isSigning ? (
            <>Generating Signature...</>
          ) : isSigned ? (
            <><ShieldCheck size={18} /> Pack Signed & Approved</>
          ) : (
            <><PenTool size={18} /> Sign & Approve Pack</>
          )}
        </button>
      </div>

      {!isSigned && (
        <div style={{ display: 'flex', gap: '8px', color: 'var(--color-warning)', fontSize: '0.75rem', alignItems: 'flex-start' }}>
          <AlertCircle size={14} style={{ flexShrink: 0 }} />
          <span>Unsigned packs cannot be deployed to "Restricted" or "Audit" mode environments.</span>
        </div>
      )}
    </div>
  );
};

export default PackSigning;
