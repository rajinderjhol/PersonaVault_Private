import React, { useState, useEffect } from 'react';
import styles from './TemporalContextControls.module.css';

export interface TemporalContext {
  startDate?: Date;
  endDate?: Date;
  range?: '24h' | '7d' | '30d' | 'custom';
}

interface TemporalContextControlsProps {
  onContextChange: (context: TemporalContext) => void;
}

export const TemporalContextControls: React.FC<TemporalContextControlsProps> = ({ onContextChange }) => {
  const [range, setRange] = useState<'24h' | '7d' | '30d' | 'custom'>('7d');
  const [customStart, setCustomStart] = useState<string>('');
  const [customEnd, setCustomEnd] = useState<string>('');

  // Apply default context on mount
  useEffect(() => {
    handleRangeChange('7d');
  }, []);

  const handleRangeChange = (newRange: typeof range) => {
    setRange(newRange);
    
    const now = new Date();
    let context: TemporalContext = { range: newRange };
    
    switch (newRange) {
      case '24h':
        context.startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        break;
      case '7d':
        context.startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
        break;
      case '30d':
        context.startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
        break;
      case 'custom':
        if (customStart && customEnd) {
          context.startDate = new Date(customStart);
          context.endDate = new Date(customEnd);
        }
        break;
    }
    
    if (newRange !== 'custom' || (customStart && customEnd)) {
      onContextChange(context);
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onContextChange({
        range: 'custom',
        startDate: new Date(customStart),
        endDate: new Date(customEnd)
      });
    }
  };

  return (
    <div className={styles.container}>
      <span className={styles.label}>🕐 Temporal Context</span>
      <div className={styles.buttons}>
        {(['24h', '7d', '30d', 'custom'] as const).map(r => (
          <button 
            key={r}
            className={`${styles.button} ${range === r ? styles.active : ''}`}
            onClick={() => handleRangeChange(r)}
          >
            {r.toUpperCase()}
          </button>
        ))}
      </div>
      {range === 'custom' && (
        <div className={styles.customRange}>
          <input 
            type="datetime-local" 
            className={styles.input}
            value={customStart}
            onChange={(e) => setCustomStart(e.target.value)}
          />
          <span className={styles.separator}>to</span>
          <input 
            type="datetime-local" 
            className={styles.input}
            value={customEnd}
            onChange={(e) => setCustomEnd(e.target.value)}
          />
          <button className={styles.applyBtn} onClick={handleCustomApply}>Apply</button>
        </div>
      )}
    </div>
  );
};
