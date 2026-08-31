import React, { useState, useEffect, useRef } from 'react';
import type { AgentStatus } from '../../types/agent';
import { getWebSocketService } from '../../services/websocketService';

// Simple styles
const styles = {
  container: {
    padding: '20px',
    background: '#1a1a2e',
    borderRadius: '12px',
    color: '#e0e0e0',
    fontFamily: 'monospace'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '16px',
    paddingBottom: '12px',
    borderBottom: '1px solid #333'
  },
  title: {
    fontSize: '18px',
    fontWeight: 'bold',
    color: '#4fc3f7'
  },
  status: {
    fontSize: '14px',
    padding: '4px 12px',
    borderRadius: '12px'
  },
  connected: {
    background: '#1b5e20',
    color: '#81c784'
  },
  disconnected: {
    background: '#4a148c',
    color: '#ce93d8'
  },
  agentList: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '12px',
    maxHeight: '400px',
    overflowY: 'auto' as const
  },
  agentCard: {
    background: '#16213e',
    padding: '12px',
    borderRadius: '8px',
    borderLeft: '3px solid #4fc3f7'
  },
  agentHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '8px'
  },
  agentName: {
    fontWeight: 'bold',
    fontSize: '14px',
    color: '#4fc3f7'
  },
  agentStatus: {
    fontSize: '12px',
    padding: '2px 8px',
    borderRadius: '10px',
    textTransform: 'uppercase' as const
  },
  thinking: {
    background: '#e65100',
    color: '#ffcc80'
  },
  active: {
    background: '#1b5e20',
    color: '#81c784'
  },
  completed: {
    background: '#0d47a1',
    color: '#64b5f6'
  },
  error: {
    background: '#b71c1c',
    color: '#ef9a9a'
  },
  agentContent: {
    fontSize: '13px',
    color: '#b0b0b0',
    marginBottom: '8px'
  },
  agentConfidence: {
    fontSize: '12px',
    color: '#ffa726',
    marginBottom: '4px'
  },
  agentTimestamp: {
    fontSize: '11px',
    color: '#616161'
  },
  emptyState: {
    textAlign: 'center' as const,
    padding: '40px',
    color: '#616161'
  }
};

export const AgentSwarmUI: React.FC = () => {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    // Get the WebSocket service
    const wsService = getWebSocketService();
    
    // Connect to WebSocket
    wsService.connect();
    
    // Check connection status
    setIsConnected(wsService.isConnected());

    // Subscribe to agent status updates
    const unsubscribe = wsService.subscribe((status: AgentStatus) => {
      console.log('Agent status update:', status);
      setAgents(prev => {
        const existing = prev.findIndex(a => a.id === status.id);
        if (existing >= 0) {
          const updated = [...prev];
          updated[existing] = status;
          return updated;
        }
        return [...prev, status];
      });
    });

    unsubscribeRef.current = unsubscribe;

    // Check connection status periodically
    const interval = setInterval(() => {
      setIsConnected(wsService.isConnected());
    }, 3000);

    // Cleanup on unmount
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
      clearInterval(interval);
    };
  }, []);

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <span style={styles.title}>🐝 Agent Swarm</span>
        <span style={{
          ...styles.status,
          ...(isConnected ? styles.connected : styles.disconnected)
        }}>
          {isConnected ? '● Connected' : '○ Disconnected'}
        </span>
      </div>
      <div style={styles.agentList}>
        {agents.length === 0 ? (
          <div style={styles.emptyState}>
            <p>No active agents</p>
            <p style={{ fontSize: '12px' }}>Waiting for agent activity...</p>
          </div>
        ) : (
          agents.map((agent) => (
            <div key={agent.id} style={styles.agentCard}>
              <div style={styles.agentHeader}>
                <span style={styles.agentName}>{agent.agentName}</span>
                <span style={{
                  ...styles.agentStatus,
                  ...(agent.status === 'thinking' ? styles.thinking :
                     agent.status === 'active' ? styles.active :
                     agent.status === 'completed' ? styles.completed :
                     styles.error)
                }}>
                  {agent.status}
                </span>
              </div>
              <div style={styles.agentContent}>{agent.content}</div>
              {agent.confidence !== undefined && (
                <div style={styles.agentConfidence}>
                  Confidence: {Math.round(agent.confidence * 100)}%
                </div>
              )}
              <div style={styles.agentTimestamp}>
                {new Date(agent.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AgentSwarmUI;
