import React from 'react';
import { MemoryLayer } from '../../api/chat';

interface MemoryAttributionProps {
  layer: MemoryLayer;
  confidence: number;
  source: string;
}

const MEMORY_CONFIG = {
  ice: {
    icon: '🧊',
    label: 'Crystallized Memory',
    color: '#4d96ff',
    description: '10,000:1 compressed pattern'
  },
  liquid: {
    icon: '💧',
    label: 'Liquid Memory',
    color: '#ffd93d',
    description: 'Recent episodic context'
  },
  gas: {
    icon: '🌫️',
    label: 'Gas Memory',
    color: '#ff6b6b',
    description: 'Working memory (volatile)'
  },
  realtime: {
    icon: '⚡',
    label: 'Real-time Reasoning',
    color: '#6bcb77',
    description: 'Live generation'
  }
};

export const MemoryAttribution: React.FC<MemoryAttributionProps> = ({ 
  layer, 
  confidence, 
  source 
}) => {
  const config = MEMORY_CONFIG[layer];
  if (!config) return null;

  return (
    <div 
      className={`memory-attribution ${layer}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '4px 12px',
        borderRadius: '20px',
        background: `rgba(15, 23, 42, 0.6)`,
        border: `1px solid ${config.color}33`,
        fontSize: '0.75rem',
        marginTop: '6px',
        width: 'fit-content'
      }}
    >
      <span style={{ fontSize: '1rem' }}>{config.icon}</span>
      <span style={{ fontWeight: 500, color: config.color }}>
        {config.label}
      </span>
      <span style={{ color: 'var(--color-text-muted)' }}>·</span>
      <span style={{ color: 'var(--color-text-secondary)' }}>
        {confidence}% confidence
      </span>
      {layer === 'ice' && (
        <span style={{ 
          background: config.color + '22', 
          padding: '0 8px', 
          borderRadius: '12px',
          fontSize: '0.65rem',
          fontWeight: 600,
          color: config.color
        }}>
          10,000:1
        </span>
      )}
      <span style={{ color: 'var(--color-text-muted)', fontSize: '0.65rem' }}>
        {source}
      </span>
    </div>
  );
};
