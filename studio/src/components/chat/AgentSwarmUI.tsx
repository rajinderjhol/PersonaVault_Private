import React, { useState, useEffect, useMemo, useRef } from 'react';
import { getWebSocketService, AgentStatus } from '../../services/websocketService';
import styles from './AgentSwarmUI.module.css';

interface AgentSwarmUIProps {
  initialMessages?: AgentStatus[];
  isActive?: boolean;
  onAgentClick?: (agent: AgentStatus) => void;
}

export const AgentSwarmUI: React.FC<AgentSwarmUIProps> = ({ 
  initialMessages = [],
  isActive = false,
  onAgentClick 
}) => {
  const [messages, setMessages] = useState<AgentStatus[]>(initialMessages);
  const [expanded, setExpanded] = useState<boolean>(true);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const currentTemporalContext = useMemo(() => {
    // Find the latest temporal context from agent messages
    const lastWithContext = messages
      .filter(m => m.temporalContext)
      .pop();
    return lastWithContext?.temporalContext || null;
  }, [messages]);

  // WebSocket subscription
  useEffect(() => {
    if (!isActive) return;

    const ws = getWebSocketService();
    ws.connect();

    const unsubscribe = ws.subscribe((newStatus: AgentStatus) => {
      setMessages(prev => {
        // Update if message already exists, otherwise add
        const index = prev.findIndex(m => m.id === newStatus.id);
        if (index >= 0) {
          const updated = [...prev];
          updated[index] = newStatus;
          return updated;
        }
        return [...prev, newStatus];
      });
    });

    return () => {
      unsubscribe();
      ws.disconnect();
    };
  }, [isActive]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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
    return messages.filter(m => m.status === 'active' || m.status === 'thinking').length;
  }, [messages]);

  return (
    <div className={`${styles.agentSwarmUI} ${isActive ? styles.active : ''}`}>
      <div className={styles.swarmHeader} onClick={() => setExpanded(!expanded)}>
        <div className={styles.swarmTitle}>
          <span className={styles.swarmIcon}>🐝</span>
          <span>Agent Swarm</span>
          <span className={styles.agentCount}>{messages.length} agents</span>
          {isActive && (
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
              {currentTemporalContext.originalExpression && (
                <span className={styles.originalQuery}>"{currentTemporalContext.originalExpression}"</span>
              )}
            </div>
          )}
          <button className={styles.expandBtn}>
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className={styles.swarmContent}>
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
                {currentTemporalContext.intervalType && (
                  <div className={styles.contextItem}>
                    <span className={styles.label}>Type:</span>
                    <span className={styles.value}>{currentTemporalContext.intervalType}</span>
                  </div>
                )}
                {currentTemporalContext.daysSpan && (
                  <div className={styles.contextItem}>
                    <span className={styles.label}>Span:</span>
                    <span className={styles.value}>{currentTemporalContext.daysSpan} days</span>
                  </div>
                )}
                {currentTemporalContext.originalExpression && (
                  <div className={`${styles.contextItem} ${styles.original}`}>
                    <span className={styles.label}>Query:</span>
                    <span className={`${styles.value} ${styles.highlight}`}>
                      "{currentTemporalContext.originalExpression}"
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className={styles.noContext}>
                <span>No temporal filter active</span>
                <span className={styles.hint}>Ask about specific time ranges like "last week" or "yesterday"</span>
              </div>
            )}
          </div>

          <div className={styles.agentMessages}>
            <h5>🤖 Agent Activity</h5>
            <div className={styles.messagesList}>
              {messages.map(msg => (
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
                      <span className={styles.agentIcon}>{getAgentIcon(msg.agentType)}</span>
                      {msg.agentName}
                      {msg.temporalContext && (
                        <span className={styles.temporalBadge}>🕐</span>
                      )}
                      {msg.confidence && (
                        <span className={styles.confidenceBadge}>
                          {Math.round(msg.confidence * 100)}%
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
                  <div className={styles.agentContent}>{msg.content}</div>
                  {selectedAgent === msg.id && msg.temporalContext && (
                    <div className={styles.agentTemporalContext}>
                      <div className={styles.temporalDetail}>
                        <span>📅 {formatDate(msg.temporalContext.startDate)} → {formatDate(msg.temporalContext.endDate)}</span>
                      </div>
                    </div>
                  )}
                  <div className={styles.agentTimestamp}>
                    🕐 {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
