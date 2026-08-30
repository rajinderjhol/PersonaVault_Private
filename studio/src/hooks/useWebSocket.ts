/**
 * React Hook for WebSocket Management
 * Provides real-time intelligence stream to components
 */

import { useEffect, useState, useRef, useCallback } from 'react';
import { IntelligenceWebSocket, WebSocketMessage, ThoughtStep } from '../api/websocket';

interface UseWebSocketOptions {
  onThought?: (step: ThoughtStep) => void;
  onTrace?: (trace: any) => void;
  onDecision?: (decision: any) => void;
  onTransition?: (transition: any) => void;
  onError?: (error: string) => void;
  autoConnect?: boolean;
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const wsRef = useRef<IntelligenceWebSocket | null>(null);
  const isMounted = useRef(true);

  const {
    onThought,
    onTrace,
    onDecision,
    onTransition,
    onError,
    autoConnect = true,
  } = options;

  const connect = useCallback(() => {
    if (wsRef.current?.isConnectedState()) {
      return;
    }

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/thermodynamics/ws';
    const ws = new IntelligenceWebSocket(wsUrl);
    
    ws.onMessage((msg: WebSocketMessage) => {
      if (!isMounted.current) return;
      
      setLastMessage(msg);

      switch (msg.type) {
        case 'thought':
          onThought?.(msg.data);
          break;
        case 'trace':
          onTrace?.(msg.data);
          break;
        case 'decision':
          onDecision?.(msg.data);
          break;
        case 'phase_transition':
          onTransition?.(msg.data);
          break;
        case 'error':
          onError?.(msg.data.message || 'WebSocket error');
          break;
      }
    });

    ws.connect();
    wsRef.current = ws;
    setIsConnected(true);
  }, [onThought, onTrace, onDecision, onTransition, onError]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.disconnect();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const send = useCallback((message: any) => {
    if (wsRef.current) {
      wsRef.current.send(message);
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    if (autoConnect) {
      connect();
    }

    return () => {
      isMounted.current = false;
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    connect,
    disconnect,
    send,
  };
};
