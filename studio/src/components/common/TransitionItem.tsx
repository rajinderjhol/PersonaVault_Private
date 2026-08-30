import React from 'react';

interface TransitionItemProps {
  transition: {
    type: string;
    description: string;
    timestamp: string;
  };
}

export const TransitionItem: React.FC<TransitionItemProps> = ({ transition }) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'freeze': return '⬇️';
      case 'melt': return '🔥';
      case 'evaporate': return '💨';
      case 'sublimate': return '🌫️';
      case 'snowflake': return '❄️';
      default: return '🔄';
    }
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', padding: '6px 0', borderBottom: '1px solid var(--glass-border)' }}>
      <span>{getIcon(transition.type)}</span>
      <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{transition.description}</span>
      <span style={{ color: 'var(--color-text-muted)', fontSize: '0.7rem' }}>
        {new Date(transition.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </span>
    </div>
  );
};
