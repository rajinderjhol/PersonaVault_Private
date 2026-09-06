import React, { useState, useEffect, useMemo, useRef } from 'react';
import type { AgentStatus } from '../../types/agent';
import { getWebSocketService } from '../../services/websocketService';
import { Agent } from '../../hooks/query/v2/useV2Agents';
import { ThermodynamicsData } from '../../hooks/query/v2/useV2Thermodynamics';
import styles from './AgentSwarmUI.module.css';

interface AgentSwarmUIProps {
  agents?: Agent[];
  thermodynamics?: ThermodynamicsData | null;
  isLoading?: boolean;
  onAgentClick?: (agent: any) => void;
  isActive?: boolean;
}

export const AgentSwarmUI: React.FC<AgentSwarmUIProps> = ({ 
  agents = [], 
  thermodynamics = null,
  isLoading = false,
  onAgentClick,
  isActive = false
}) => {
  const [expanded, setExpanded] = useState<boolean>(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentTemporalContext = useMemo(() => {
    // Find the latest temporal context from agent messages
    const lastWithContext = agents
      .filter(m => (m as any).temporalContext)
      .pop();
    return (lastWithContext as any)?.temporalContext || null;
  }, [agents]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [agents]);

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const getAgentIcon = (type?: string) => {
    switch (type) {
      case 'orchestrator': return '🎯';
      case 'reasoning': return '🧠';
      case 'policy': return '📋';
      case 'memory': return '💾';
      case 'action': return '⚡';
      default: return '🤖';
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'thinking': return '#eab308';
      case 'active': return '#818cf8';
      case 'completed': return '#22c55e';
      case 'error': return '#ef4444';
      default: return 'transparent';
    }
  };

  const activeCount = useMemo(() => {
    return agents.filter(m => m.status === 'active' || m.status === 'thinking').length;
  }, [agents]);

  return (
    <div className={`${styles.agentSwarmUI} ${isActive || agents.length > 0 ? styles.active : ''}`}>
      <div className={styles.swarmHeader} onClick={() => setExpanded(!expanded)}>
        <div className={styles.swarmTitle}>
          <span className={styles.swarmIcon}>🐝</span>
          <span>Agent Swarm</span>
          <span className={styles.agentCount}>{agents.length} agents</span>
          {(isActive || agents.length > 0) && (
            <span className={styles.liveBadge}>
              <span className={styles.pulseDot}></span>
              Live
            </span>
          )}
          {activeCount > 0 && (
            <span className={styles.activeCount}>{activeCount} active</span>
          )}
        </div>
        
        <div className={styles.swarmControls}>
          {currentTemporalContext && (
            <div className={styles.temporalIndicator} title="Temporal filter active">
              <span className={styles.timeIcon}>🕐</span>
              <span className={styles.timeRange}>
                {formatDate(currentTemporalContext.startDate)} - {formatDate(currentTemporalContext.endDate)}
              </span>
            </div>
          )}
          <button className={styles.expandBtn}>
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className={styles.swarmContent}>
          {/* Thermodynamics Section */}
          {thermodynamics && (
            <div className={styles.thermoSection}>
              <h5>🔥 Memory Phases</h5>
              <div className={styles.thermoGrid}>
                <div className={styles.thermoItem}>
                  <span className={styles.thermoLabel}>Gas</span>
                  <span className={styles.thermoValue}>{thermodynamics.gas}</span>
                  <div className={styles.thermoBar} style={{ width: `${(thermodynamics.gas / thermodynamics.total) * 100}%`, background: '#ff4d4d' }} />
                </div>
                <div className={styles.thermoItem}>
                  <span className={styles.thermoLabel}>Liquid</span>
                  <span className={styles.thermoValue}>{thermodynamics.liquid}</span>
                  <div className={styles.thermoBar} style={{ width: `${(thermodynamics.liquid / thermodynamics.total) * 100}%`, background: '#3399ff' }} />
                </div>
                <div className={styles.thermoItem}>
                  <span className={styles.thermoLabel}>Ice</span>
                  <span className={styles.thermoValue}>{thermodynamics.ice}</span>
                  <div className={styles.thermoBar} style={{ width: `${(thermodynamics.ice / thermodynamics.total) * 100}%`, background: '#b3e0ff' }} />
                </div>
              </div>
            </div>
          )}

          <div className={styles.temporalContextSection}>
            <h5>🕐 Temporal Context</h5>
            {currentTemporalContext ? (
              <div className={styles.contextDetails}>
                <div className={styles.contextItem}>
                  <span className={styles.label}>Range:</span>
                  <span className={styles.value}>
                    {formatDate(currentTemporalContext.startDate)} → {formatDate(currentTemporalContext.endDate)}
                  </span>
                </div>
              </div>
            ) : (
              <div className={styles.noContext}>
                <span>No temporal filter active</span>
              </div>
            )}
          </div>

          <div className={styles.agentMessages}>
            <h5>🤖 Agent Activity</h5>
            {isLoading && agents.length === 0 ? (
              <div className={styles.loading}>Loading agents...</div>
            ) : (
              <div className={styles.messagesList}>
                {agents.map(msg => (
                  <div 
                    key={msg.id} 
                    className={`${styles.agentMessage} ${selectedAgent === msg.id ? styles.selected : ''}`}
                    onClick={() => {
                      setSelectedAgent(selectedAgent === msg.id ? null : msg.id);
                      onAgentClick?.(msg);
                    }}
                  >
                    <div className={styles.agentHeader}>
                      <div className={styles.agentName}>
                        <span className={styles.agentIcon}>{getAgentIcon(msg.type)}</span>
                        {msg.name}
                        {(msg as any).confidence && (
                          <span className={styles.confidenceBadge}>
                            {Math.round((msg as any).confidence * 100)}%
                          </span>
                        )}
                      </div>
                      <div className={styles.agentStatus}>
                        <span 
                          className={styles.statusDot}
                          style={{ backgroundColor: getStatusColor(msg.status) }}
                        />
                        <span className={styles.statusText}>{msg.status || 'idle'}</span>
                      </div>
                    </div>
                    {msg.content && <div className={styles.agentContent}>{msg.content}</div>}
                    <div className={styles.agentTimestamp}>
                      🕐 {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString()}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

