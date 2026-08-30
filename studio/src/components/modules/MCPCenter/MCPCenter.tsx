import React from 'react';
import { useMCPStore } from '../../../store/mcpStore';
import { Share2, Terminal, Activity, Layers } from 'lucide-react';

const MCPCenter: React.FC = () => {
  const { tools, toggleTool } = useMCPStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Server Management */}
          <Section title="MCP Server Tools" icon={<Terminal size={18} />}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {tools.filter(t => t.type === 'server').map(tool => (
                <ToolCard key={tool.id} tool={tool} onToggle={() => toggleTool(tool.id)} />
              ))}
            </div>
          </Section>

          {/* Client Management */}
          <Section title="External MCP Clients" icon={<Share2 size={18} />}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {tools.filter(t => t.type === 'client').map(tool => (
                <ToolCard key={tool.id} tool={tool} onToggle={() => toggleTool(tool.id)} />
              ))}
            </div>
          </Section>
        </div>

        {/* Metrics Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={16} /> Ecosystem Metrics
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <MetricItem label="Active Tool Connections" value="4" />
              <MetricItem label="Total Tool Invocations" value="1,248" />
              <MetricItem label="Success Rate" value="99.4%" color="var(--color-success)" />
              <MetricItem label="Avg Latency" value="18ms" color="var(--color-gas)" />
            </div>
          </div>

          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', margin: 0 }}>Protocol Status</h3>
            <div style={{ padding: '12px', borderRadius: '8px', backgroundColor: 'rgba(0, 242, 255, 0.05)', border: '1px solid rgba(0, 242, 255, 0.1)', display: 'flex', alignItems: 'center', gap: '12px' }}>
              <Layers size={20} color="var(--color-gas)" />
              <div style={{ fontSize: '0.8rem' }}>
                <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>MCP v1.2 Active</div>
                <div style={{ color: 'var(--color-text-secondary)' }}>Secure context propagation enabled</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Section: React.FC<{ title: string, icon: React.ReactNode, children: React.ReactNode }> = ({ title, icon, children }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
    <h2 style={{ fontSize: '1.1rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
      {icon} {title}
    </h2>
    {children}
  </div>
);

const ToolCard: React.FC<{ tool: any, onToggle: () => void }> = ({ tool, onToggle }) => (
  <div style={{ 
    backgroundColor: 'var(--color-bg-secondary)', 
    padding: '20px', 
    borderRadius: '12px', 
    border: '1px solid var(--glass-border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    transition: 'all 0.2s ease'
  }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>{tool.name}</div>
      <div style={{ 
        width: '10px', 
        height: '10px', 
        borderRadius: '50%', 
        backgroundColor: tool.status === 'active' ? 'var(--color-success)' : 'var(--color-text-muted)' 
      }} />
    </div>
    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', lineHeight: 1.4, flex: 1 }}>{tool.description}</div>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
      <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
        Used {tool.usageCount} times
      </div>
      <button 
        onClick={onToggle}
        style={{
          background: 'none',
          border: '1px solid var(--glass-border)',
          color: tool.status === 'active' ? 'var(--color-error)' : 'var(--color-gas)',
          padding: '4px 10px',
          borderRadius: '4px',
          fontSize: '0.75rem',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
      >
        {tool.status === 'active' ? 'Disable' : 'Enable'}
      </button>
    </div>
  </div>
);

const MetricItem: React.FC<{ label: string, value: string, color?: string }> = ({ label, value, color }) => (
  <div>
    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>{label}</div>
    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: color || 'var(--color-text-primary)' }}>{value}</div>
  </div>
);

export default MCPCenter;
