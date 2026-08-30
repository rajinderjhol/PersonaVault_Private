import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface Agent {
  name: string;
  type: string;
  status: 'active' | 'idle' | 'error';
  confidence: number;
  config: Record<string, any>;
  capabilities: string[];
  metrics: {
    tasks_processed: number;
    success_rate: number;
    avg_latency: number;
    last_active: string;
  };
}

export const AgentConfig: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editingConfig, setEditingConfig] = useState<Record<string, any>>({});
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAgents = async () => {
    try {
      const response = await apiClient.get('/swarm/agents');
      setAgents(response.data);
      if (response.data.length > 0 && !selectedAgent) {
        setSelectedAgent(response.data[0].name);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigChange = (key: string, value: any) => {
    setEditingConfig(prev => ({ ...prev, [key]: value }));
  };

  const saveConfig = async () => {
    if (!selectedAgent) return;
    try {
      await apiClient.patch(`/swarm/agents/${selectedAgent}`, editingConfig);
      setMessage({ type: 'success', text: 'Configuration saved successfully' });
      await fetchAgents();
      setEditingConfig({});
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    }
  };

  const selected = agents.find(a => a.name === selectedAgent);

  if (isLoading) {
    return <div className="agent-loading">Loading agents...</div>;
  }

  return (
    <div className="agent-config">
      {/* Agent List */}
      <div className="agent-list">
        <h4>🐝 Agent Swarm</h4>
        {agents.map(agent => (
          <div 
            key={agent.name}
            className={`agent-item ${agent.name === selectedAgent ? 'selected' : ''}`}
            onClick={() => setSelectedAgent(agent.name)}
          >
            <div className="agent-info">
              <span className="agent-name">{agent.name}</span>
              <span className={`agent-status ${agent.status}`}>
                {agent.status === 'active' ? '●' : '○'} {agent.status}
              </span>
            </div>
            <div className="agent-stats">
              <span className="agent-confidence">{agent.confidence}%</span>
              <span className="agent-tasks">{agent.metrics?.tasks_processed || 0}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Agent Details */}
      {selected && (
        <div className="agent-details">
          <div className="details-header">
            <h3>{selected.name}</h3>
            <span className={`status ${selected.status}`}>{selected.status}</span>
          </div>

          <div className="details-metrics">
            <div className="metric-card">
              <span className="metric-label">Tasks</span>
              <span className="metric-value">{selected.metrics?.tasks_processed || 0}</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Success Rate</span>
              <span className="metric-value">{selected.metrics?.success_rate || 0}%</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Avg Latency</span>
              <span className="metric-value">{selected.metrics?.avg_latency || 0}ms</span>
            </div>
            <div className="metric-card">
              <span className="metric-label">Confidence</span>
              <span className="metric-value">{selected.confidence}%</span>
            </div>
          </div>

          <div className="details-config">
            <h4>⚙️ Configuration</h4>
            {Object.entries(selected.config || {}).map(([key, value]) => (
              <div key={key} className="config-field">
                <label>{key}</label>
                {typeof value === 'boolean' ? (
                  <input
                    type="checkbox"
                    checked={editingConfig[key] ?? value}
                    onChange={(e) => handleConfigChange(key, e.target.checked)}
                  />
                ) : typeof value === 'number' ? (
                  <input
                    type="number"
                    value={editingConfig[key] ?? value}
                    onChange={(e) => handleConfigChange(key, parseFloat(e.target.value))}
                  />
                ) : (
                  <input
                    type="text"
                    value={editingConfig[key] ?? value}
                    onChange={(e) => handleConfigChange(key, e.target.value)}
                  />
                )}
              </div>
            ))}
            <button className="btn-save" onClick={saveConfig}>
              💾 Save Configuration
            </button>
          </div>

          <div className="details-capabilities">
            <h4>🛠️ Capabilities</h4>
            <div className="capability-tags">
              {(selected.capabilities || []).map(cap => (
                <span key={cap} className="capability-tag">{cap}</span>
              ))}
            </div>
          </div>

          {message && (
            <div className={`config-message ${message.type}`}>
              {message.text}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
