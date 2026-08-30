import React, { useState } from 'react';
import ChatInterface from './Chat/ChatInterface';
import ThoughtNarrative from './Chat/ThoughtNarrative';
import { ProviderSelect } from './ProviderSelect';

const CognitiveLab: React.FC = () => {
  const [provider, setProvider] = useState('ollama');
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 300px',
      gap: '24px',
      height: 'calc(100vh - var(--header-height) - var(--footer-height) - 48px)',
    }}>
      {/* Interaction Column */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        gap: '20px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>🧠 Cognitive Lab</h2>
          <ProviderSelect value={provider} onChange={setProvider} />
        </div>
        <ChatInterface />
      </div>

      {/* Thought Narrative Sidebar (Internal to Lab) */}
      <div style={{
        backgroundColor: 'rgba(15, 23, 42, 0.3)',
        borderRadius: '16px',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        <div style={{
          padding: '16px',
          borderBottom: '1px solid var(--glass-border)',
          backgroundColor: 'rgba(30, 41, 59, 0.5)',
          fontSize: '0.9rem',
          fontWeight: 600,
          color: 'var(--color-text-secondary)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          Thought Narrative
        </div>
        <ThoughtNarrative />
      </div>
    </div>
  );
};

export default CognitiveLab;
