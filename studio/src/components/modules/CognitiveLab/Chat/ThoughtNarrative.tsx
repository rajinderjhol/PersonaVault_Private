import React from 'react';
import { useChatStore } from '../../../../store/chatStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal } from 'lucide-react';

const ThoughtNarrative: React.FC = () => {
  const { messages } = useChatStore();
  
  // Extract all thoughts from assistant messages
  const assistantMessages = messages.filter(m => m.role === 'assistant' && m.thought);
  const latestThought = assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1].thought : null;

  return (
    <div style={{
      flex: 1,
      padding: '16px',
      overflowY: 'auto',
      display: 'flex',
      flexDirection: 'column',
      gap: '12px',
      fontFamily: 'monospace',
      fontSize: '0.8rem'
    }}>
      <AnimatePresence mode="wait">
        {latestThought ? (
          <motion.div
            key={latestThought}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
          >
            {latestThought.split('...').map((t: string, i: number) => t.trim() && (
              <div key={i} style={{ display: 'flex', gap: '8px', color: i === latestThought.split('...').length - 2 ? 'var(--color-gas)' : 'var(--color-text-muted)' }}>
                <span style={{ opacity: 0.5 }}>{'>'}</span>
                <span>{t.trim()}...</span>
              </div>
            ))}
            <motion.div
              animate={{ opacity: [0, 1, 0] }}
              transition={{ repeat: Infinity, duration: 1 }}
              style={{ width: '8px', height: '14px', backgroundColor: 'var(--color-gas)', display: 'inline-block' }}
            />
          </motion.div>
        ) : (
          <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', marginTop: '40px' }}>
            <Terminal size={32} style={{ opacity: 0.2, marginBottom: '12px' }} />
            <div>Standby for cognitive stream...</div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ThoughtNarrative;
