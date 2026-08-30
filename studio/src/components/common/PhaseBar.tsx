import React from 'react';

interface PhaseBarProps {
  label: string;
  value: number;
  total: number;
  color: string;
}

export const PhaseBar: React.FC<PhaseBarProps> = ({ label, value, total, color }) => {
  const percentage = total > 0 ? Math.max((value / total) * 100, 0.5) : 0;

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '4px' }}>
        <span>{label}</span>
        <span>{value}</span>
      </div>
      <div style={{ height: '8px', backgroundColor: 'var(--color-bg-secondary)', borderRadius: '4px', overflow: 'hidden' }}>
        <div
          style={{
            height: '100%',
            width: `${percentage}%`,
            backgroundColor: color,
            transition: 'width 0.3s ease'
          }}
        />
      </div>
    </div>
  );
};
