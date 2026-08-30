import React from 'react';
import { motion } from 'framer-motion';
import { Zap, Shrink } from 'lucide-react';

const CrystallizationDashboard: React.FC = () => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(2, 1fr)',
      gap: '20px'
    }}>
      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderRadius: '16px',
        padding: '24px',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-ice)' }}>
          <Shrink size={20} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase' }}>Intelligence Compression</span>
        </div>
        <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
          10,000:1
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          Crystallized patterns represent 99.9% reduction in inference overhead.
        </div>
        <div style={{ height: '8px', backgroundColor: 'var(--color-bg-tertiary)', borderRadius: '4px', overflow: 'hidden' }}>
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: '100%' }}
            transition={{ duration: 2 }}
            style={{ height: '100%', background: 'linear-gradient(90deg, var(--color-liquid) 0%, var(--color-ice) 100%)' }}
          />
        </div>
      </div>

      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderRadius: '16px',
        padding: '24px',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-gas)' }}>
          <Zap size={20} />
          <span style={{ fontWeight: 600, fontSize: '0.9rem', textTransform: 'uppercase' }}>Reinforcement Rate</span>
        </div>
        <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--color-text-primary)' }}>
          +12.4%
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>
          Confidence gains from pattern reinforcement in the last 24 hours.
        </div>
        <div style={{ display: 'flex', gap: '4px', alignItems: 'flex-end', height: '32px' }}>
          {[40, 60, 45, 80, 55, 90, 75, 100].map((h, i) => (
            <motion.div 
              key={i}
              initial={{ height: 0 }}
              animate={{ height: `${h}%` }}
              transition={{ delay: i * 0.1 }}
              style={{ flex: 1, backgroundColor: 'var(--color-gas)', borderRadius: '2px 2px 0 0', opacity: 0.5 + (i * 0.05) }}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default CrystallizationDashboard;
