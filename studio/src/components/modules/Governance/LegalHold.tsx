import React, { useState } from 'react';
import { Gavel, Snowflake, Play } from 'lucide-react';
import { useTraceStore } from '../../../store/traceStore';

const LegalHold: React.FC = () => {
  const { history } = useTraceStore();
  const [heldTraces, setHeldTraces] = useState<string[]>([]);

  const toggleHold = (id: string) => {
    setHeldTraces(prev => 
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Gavel size={18} color="var(--color-warning)" /> Active Legal Holds
        </h3>
        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
          {heldTraces.length} traces frozen for discovery
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {history.length > 0 ? history.map(trace => (
          <div key={trace.id} style={{
            backgroundColor: 'var(--color-bg-tertiary)',
            padding: '12px 16px',
            borderRadius: '10px',
            border: `1px solid ${heldTraces.includes(trace.id) ? 'var(--color-warning)' : 'var(--glass-border)'}`,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-primary)' }}>Trace #{trace.id}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{new Date(trace.timestamp).toLocaleString()}</div>
            </div>
            <button 
              onClick={() => toggleHold(trace.id)}
              style={{
                backgroundColor: heldTraces.includes(trace.id) ? 'var(--color-warning)' : 'transparent',
                color: heldTraces.includes(trace.id) ? 'var(--color-bg-primary)' : 'var(--color-text-secondary)',
                border: `1px solid ${heldTraces.includes(trace.id) ? 'var(--color-warning)' : 'var(--glass-border)'}`,
                padding: '4px 12px',
                borderRadius: '6px',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              {heldTraces.includes(trace.id) ? <Snowflake size={12} /> : <Play size={12} />}
              {heldTraces.includes(trace.id) ? 'Frozen' : 'Hold'}
            </button>
          </div>
        )) : (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
            No decision traces available for hold.
          </div>
        )}
      </div>
    </div>
  );
};

export default LegalHold;
