import React from 'react';
import { useCompilerStore } from '../../../store/compilerStore';
import { Terminal, Save, Play, FileCode, CheckCircle, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const PatternCompiler: React.FC = () => {
  const { packs, activePackId, updatePack, setActivePack, compilePack, isCompiling, compilationLog } = useCompilerStore();
  const activePack = packs.find(p => p.id === activePackId) || packs[0];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr 350px', gap: '20px', height: 'calc(100vh - 160px)' }}>
      {/* Sidebar: Pack List */}
      <div style={{ backgroundColor: 'var(--color-bg-secondary)', borderRadius: '12px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--glass-border)', fontSize: '0.85rem', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
          Behavior Packs
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '8px' }}>
          {packs.map(pack => (
            <div 
              key={pack.id} 
              onClick={() => setActivePack(pack.id)}
              style={{
                padding: '12px',
                borderRadius: '8px',
                cursor: 'pointer',
                backgroundColor: activePackId === pack.id ? 'rgba(0, 242, 255, 0.1)' : 'transparent',
                color: activePackId === pack.id ? 'var(--color-gas)' : 'var(--color-text-secondary)',
                marginBottom: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                fontSize: '0.85rem'
              }}
            >
              <FileCode size={16} />
              <div style={{ flex: 1 }}>{pack.name}</div>
              <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: pack.status === 'compiled' ? 'var(--color-success)' : 'var(--color-warning)' }} />
            </div>
          ))}
        </div>
      </div>

      {/* Main Area: YAML IDE */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ 
          flex: 1, 
          backgroundColor: '#0f172a', 
          borderRadius: '12px', 
          border: '1px solid var(--glass-border)', 
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div style={{ padding: '12px 20px', backgroundColor: 'rgba(30, 41, 59, 0.5)', borderBottom: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--color-text-secondary)' }}>
              {activePack.domain}/pack.yaml
            </div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}><Save size={16} /></button>
              <button 
                onClick={() => compilePack(activePack.id)}
                disabled={isCompiling}
                style={{ 
                  backgroundColor: 'var(--color-gas)', 
                  color: 'var(--color-bg-primary)', 
                  border: 'none', 
                  borderRadius: '4px', 
                  padding: '4px 12px', 
                  fontSize: '0.75rem', 
                  fontWeight: 700, 
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {isCompiling ? 'Compiling...' : 'Compile'} <Play size={12} />
              </button>
            </div>
          </div>
          <textarea 
            value={activePack.content}
            onChange={(e) => updatePack(activePack.id, e.target.value)}
            spellCheck={false}
            style={{
              flex: 1,
              background: 'none',
              border: 'none',
              padding: '20px',
              color: '#94a3b8',
              fontFamily: 'monospace',
              fontSize: '0.9rem',
              lineHeight: 1.6,
              outline: 'none',
              resize: 'none'
            }}
          />
        </div>
      </div>

      {/* Right Area: Compiler Hub */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ 
          flex: 1, 
          backgroundColor: 'var(--color-bg-secondary)', 
          borderRadius: '12px', 
          border: '1px solid var(--glass-border)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}>
          <div style={{ padding: '16px', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Terminal size={16} color="var(--color-gas)" />
            <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>Compiler Hub</span>
          </div>
          <div style={{ flex: 1, padding: '16px', fontFamily: 'monospace', fontSize: '0.75rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {compilationLog.map((log, i) => (
              <div key={i} style={{ color: log.includes('complete') ? 'var(--color-success)' : 'var(--color-text-secondary)' }}>
                {log}
              </div>
            ))}
            {isCompiling && (
              <motion.div 
                animate={{ opacity: [0, 1, 0] }}
                transition={{ repeat: Infinity, duration: 1 }}
                style={{ color: 'var(--color-gas)' }}
              >
                {'>'} Compiling behavior logic...
              </motion.div>
            )}
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '20px', borderRadius: '12px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h3 style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', margin: 0 }}>Validation Results</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-success)', fontSize: '0.85rem' }}>
            <CheckCircle size={16} /> 12 Policies Valid
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-gas)', fontSize: '0.85rem' }}>
            <CheckCircle size={16} /> Schema Alignment 100%
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>
            <AlertCircle size={16} /> 0 Warnings
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatternCompiler;
