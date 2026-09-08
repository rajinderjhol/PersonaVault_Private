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

    // Get the session token
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(';').shift();
      return null;
    };
    const sessionToken = getCookie('session_id');

    // Build the WebSocket URL
    const buildWsUrl = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      
      // Use the standard /v2 prefix which now has ws: true in vite.config.ts
      let url = `${protocol}//${host}/v2/environments/${currentEnvId}/agents/ws`;
      
      if (sessionToken) {
        url += `?token=${sessionToken}`;
      }
      return url;
    };

    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;
    let retryCount = 0;

    const connect = () => {
      const wsUrl = buildWsUrl();
      console.log(`🔌 Attempting WebSocket connection (attempt ${retryCount + 1}) to:`, wsUrl.split('?')[0]);

      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          setIsConnected(true);
          retryCount = 0;
          console.log('✅ Agent WebSocket connected successfully');
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            // Handle both array of agents (new backend) and specific events (old/complex backend)
            if (Array.isArray(data)) {
              setAgents(data);
              return;
            }

            if (data.type === 'agent_status') {
              setAgents(prev => {
                const existingIndex = prev.findIndex(a => a.agentId === data.agentId);
                if (existingIndex >= 0) {
                  const updated = [...prev];
                  updated[existingIndex] = { ...updated[existingIndex], ...data.payload };
                  return updated;
                }
                return [...prev, { ...data.payload, agentId: data.agentId }];
              });
            }
          } catch (error) {
            console.error('❌ Failed to parse WebSocket message:', error);
          }
        };

        ws.onclose = (event) => {
          setIsConnected(false);
          console.warn(`⚠️ WebSocket closed (code: ${event.code}, reason: ${event.reason || 'none'})`);
          
          // Exponential backoff for reconnection
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
          retryCount++;
          
          reconnectTimer = setTimeout(() => {
            console.log('🔄 Reconnecting WebSocket...');
            connect();
          }, delay);
        };

        ws.onerror = (error) => {
          console.error('❌ WebSocket error details:', error);
          // Don't close manually, onclose will handle it
        };
      } catch (err) {
        console.error('❌ WebSocket setup critical failure:', err);
      }
    };

    connect();

    return () => {
      console.log('🔌 Cleaning up WebSocket connection');
      if (ws) {
        ws.onclose = null; // Prevent reconnection loop during unmount
        ws.close();
      }
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [currentEnvId]);

  return { agents, isConnected };
};
