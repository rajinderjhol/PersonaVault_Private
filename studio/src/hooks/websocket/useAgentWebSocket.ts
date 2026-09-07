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

    const currentHost = window.location.host;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // In Cloud Shell, the frontend and backend are on different ports (and subdomains)
    // We attempt to get the session token from document.cookie.
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(';').shift();
      return null;
    };
    const sessionToken = getCookie('session_id');
    console.log('🔑 Retrieved session token:', sessionToken ? 'Found' : 'Not Found');

    let wsUrl: string;

    if (import.meta.env.VITE_WS_URL) {
      wsUrl = `${import.meta.env.VITE_WS_URL.replace('http', 'ws')}/v2/environments/${currentEnvId}/ws/agents`;
    } else if (currentHost.includes('5173-cs-')) {
      const backendHost = currentHost.replace('5173-cs-', '8000-cs-');
      wsUrl = `${protocol}//${backendHost}/v2/environments/${currentEnvId}/ws/agents`;
    } else {
      wsUrl = `${protocol}//${currentHost}/v2/environments/${currentEnvId}/ws/agents`;
    }

    // Append token as query parameter
    if (sessionToken) {
      wsUrl += `?token=${sessionToken}`;
    } else {
      console.warn('⚠️ No session token found for WebSocket connection');
    }

    console.log('🔌 Attempting WebSocket connection to:', wsUrl.replace(sessionToken || '', '***'));

    let ws: WebSocket;
    let reconnectTimer: any;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
          console.log('🔌 Agent WebSocket connected to:', wsUrl);
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
      } catch (err) {
        console.error('WebSocket setup failed:', err);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [currentEnvId]);

  return { agents, isConnected };
};
