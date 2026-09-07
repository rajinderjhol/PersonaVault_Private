import { useEffect, useState } from 'react';
import { useEnvironmentStore } from '../../store/environmentStore';

export interface AgentUpdate {
  agentId: string;
  status: 'active' | 'idle' | 'thinking' | 'error' | 'busy';
  currentTask?: string;
  lastActivity: string;
  memoryPhase?: string;
  name?: string;
}

export const useAgentWebSocket = () => {
  const { currentEnvId } = useEnvironmentStore();
  const [agents, setAgents] = useState<AgentUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!currentEnvId) return;

    const wsUrl = import.meta.env.VITE_WS_URL
      ? `${import.meta.env.VITE_WS_URL.replace('http', 'ws')}/v2/environments/${currentEnvId}/ws/agents`
      : `/v2/environments/${currentEnvId}/ws/agents`;

    let ws: WebSocket;
    let reconnectTimer: any;

    const connect = () => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('🔌 Agent WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          switch (data.type) {
            case 'agent_status':
              setAgents(prev => {
                const existingIndex = prev.findIndex(a => a.agentId === data.agentId);
                if (existingIndex >= 0) {
                  const updated = [...prev];
                  updated[existingIndex] = { ...updated[existingIndex], ...data.payload };
                  return updated;
                }
                return [...prev, { ...data.payload, agentId: data.agentId }];
              });
              break;
            case 'phase_transition':
              // This could trigger a refresh of thermodynamics data via queryClient
              console.log('🔥 Phase transition detected:', data.payload);
              break;
            case 'decision_created':
              console.log('🎯 Decision created:', data.payload);
              break;
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('🔌 Agent WebSocket disconnected, retrying in 3s...');
        reconnectTimer = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [currentEnvId]);

  return { agents, isConnected };
};
