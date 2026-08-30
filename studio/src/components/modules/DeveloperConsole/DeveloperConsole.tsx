import React, { useState } from 'react';
import { Terminal, Globe, RefreshCw, CheckCircle } from 'lucide-react';
import { motion } from 'framer-motion';

const DeveloperConsole: React.FC = () => {
  const [activeTab, setActiveModule] = useState<'api' | 'events' | 'sdk'>('api');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', height: '100%' }}>
      <div style={{ display: 'flex', gap: '12px' }}>
        <TabButton active={activeTab === 'api'} label="API Explorer" icon={<Globe size={16} />} onClick={() => setActiveModule('api')} />
        <TabButton active={activeTab === 'events'} label="WebSocket Monitor" icon={<RefreshCw size={16} />} onClick={() => setActiveModule('events')} />
        <TabButton active={activeTab === 'sdk'} label="SDK/CLI Status" icon={<Terminal size={16} />} onClick={() => setActiveModule('sdk')} />
      </div>

      <div style={{ flex: 1, backgroundColor: 'var(--color-bg-secondary)', borderRadius: '16px', border: '1px solid var(--glass-border)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'api' && <APIExplorer />}
        {activeTab === 'events' && <WebSocketMonitor />}
        {activeTab === 'sdk' && <SDKStatus />}
      </div>
    </div>
  );
};

const TabButton: React.FC<{ active: boolean, label: string, icon: React.ReactNode, onClick: () => void }> = ({ active, label, icon, onClick }) => (
  <button 
    onClick={onClick}
    style={{
      backgroundColor: active ? 'rgba(0, 242, 255, 0.1)' : 'var(--color-bg-secondary)',
      color: active ? 'var(--color-gas)' : 'var(--color-text-secondary)',
      border: `1px solid ${active ? 'var(--color-gas)' : 'var(--glass-border)'}`,
      padding: '8px 20px',
      borderRadius: '8px',
      display: 'flex',
      alignItems: 'center',
      gap: '10px',
      fontSize: '0.85rem',
      fontWeight: 600,
      cursor: 'pointer',
      transition: 'all 0.2s ease'
    }}
  >
    {icon} {label}
  </button>
);

const APIExplorer: React.FC = () => {
  const [method, setMethod] = useState('GET');
  const [endpoint, setEndpoint] = useState('/api/v1/traces/latest');

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0', flex: 1 }}>
      <div style={{ borderRight: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', padding: '24px', gap: '20px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          <select 
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            style={{ backgroundColor: 'var(--color-bg-tertiary)', border: '1px solid var(--glass-border)', color: 'var(--color-gas)', padding: '10px', borderRadius: '8px', fontWeight: 700, fontSize: '0.85rem' }}
          >
            <option>GET</option>
            <option>POST</option>
            <option>PUT</option>
            <option>DELETE</option>
          </select>
          <input 
            value={endpoint}
            onChange={(e) => setEndpoint(e.target.value)}
            style={{ flex: 1, backgroundColor: 'var(--color-bg-primary)', border: '1px solid var(--glass-border)', color: 'white', padding: '10px 16px', borderRadius: '8px', fontFamily: 'monospace', fontSize: '0.85rem' }} 
          />
          <button style={{ backgroundColor: 'var(--color-gas)', color: 'var(--color-bg-primary)', border: 'none', borderRadius: '8px', padding: '0 20px', fontWeight: 700, cursor: 'pointer' }}>
            Run
          </button>
        </div>

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Request Body</div>
          <textarea 
            placeholder="{}"
            style={{ flex: 1, backgroundColor: '#0f172a', border: '1px solid var(--glass-border)', borderRadius: '8px', padding: '16px', color: '#94a3b8', fontFamily: 'monospace', fontSize: '0.85rem', resize: 'none', outline: 'none' }}
          />
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', backgroundColor: '#020617', padding: '24px', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>Response Output</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-success)', fontWeight: 600 }}>200 OK - 42ms</div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', color: '#6ee7b7', fontFamily: 'monospace', fontSize: '0.8rem', lineHeight: 1.6 }}>
          <pre>{JSON.stringify({
            status: "success",
            trace_id: "824",
            timestamp: 1725019200,
            perception: {
              intent: "data_access",
              confidence: 0.98
            },
            evidence: [
              "episodic_memory_124",
              "security_policy_v2.1"
            ],
            signals: {
              type: "outbound_transfer",
              volume: "240MB"
            }
          }, null, 2)}</pre>
        </div>
      </div>
    </div>
  );
};

const WebSocketMonitor: React.FC = () => (
  <div style={{ flex: 1, backgroundColor: '#020617', padding: '20px', fontFamily: 'monospace', fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
    <LogEntry type="event" msg="[SOCKET] Connected to wss://personavault/v1/stream" />
    <LogEntry type="data" msg="[RECV] {'type': 'perception', 'id': '824', 'intent': 'access'}" />
    <LogEntry type="data" msg="[RECV] {'type': 'evidence', 'id': '824', 'nodes': 2}" />
    <LogEntry type="event" msg="[CRYSTAL] Pattern #42 updated via consolidation loop" color="var(--color-ice)" />
    <LogEntry type="data" msg="[RECV] {'type': 'trace_complete', 'id': '824'}" />
    <motion.div animate={{ opacity: [0.3, 1, 0.3] }} transition={{ repeat: Infinity, duration: 1.5 }} style={{ color: 'var(--color-gas)' }}>
      {'>'} Monitoring live decision events...
    </motion.div>
  </div>
);

const LogEntry: React.FC<{ type: string, msg: string, color?: string }> = ({ type, msg, color }) => (
  <div style={{ display: 'flex', gap: '12px', color: color || '#94a3b8' }}>
    <span style={{ opacity: 0.4 }}>[{new Date().toLocaleTimeString()}]</span>
    <span style={{ color: type === 'event' ? 'var(--color-gas)' : '#cbd5e1', fontWeight: 600 }}>[{type.toUpperCase()}]</span>
    <span>{msg}</span>
  </div>
);

const SDKStatus: React.FC = () => (
  <div style={{ padding: '40px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' }}>
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <h3 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>Python SDK</h3>
      <div style={{ backgroundColor: 'var(--color-bg-tertiary)', padding: '20px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Current Version</span>
          <span style={{ color: 'var(--color-gas)', fontWeight: 700 }}>v2.4.1</span>
        </div>
        <code style={{ display: 'block', backgroundColor: '#000', padding: '12px', borderRadius: '6px', fontSize: '0.8rem', color: '#fff' }}>
          pip install personavault
        </code>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-success)', fontSize: '0.9rem' }}>
        <CheckCircle size={16} /> Runtime Verified
      </div>
    </div>

    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <h3 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0 }}>PV CLI</h3>
      <div style={{ backgroundColor: 'var(--color-bg-tertiary)', padding: '20px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>Status</span>
          <span style={{ color: 'var(--color-success)', fontWeight: 700 }}>Active</span>
        </div>
        <code style={{ display: 'block', backgroundColor: '#000', padding: '12px', borderRadius: '6px', fontSize: '0.8rem', color: '#fff' }}>
          pv trace tail --id 824
        </code>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-success)', fontSize: '0.9rem' }}>
        <CheckCircle size={16} /> Symlink Active
      </div>
    </div>
  </div>
);

export default DeveloperConsole;
