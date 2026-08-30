export interface AgentStatus {
  id: string;
  agentName: string;
  agentType?: string;
  content: string;
  timestamp: string;
  status: 'thinking' | 'active' | 'completed' | 'error';
  confidence?: number;
  temporalContext?: {
    startDate: string;
    endDate: string;
    intervalType: string;
    originalExpression?: string;
    daysSpan?: number;
  };
}

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 3000;
  private listeners: ((status: AgentStatus) => void)[] = [];

  constructor(private url: string) {}

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected for agent status');
        this.reconnectAttempts = 0;
      };
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach(listener => listener(data));
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect();
      };
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Reconnecting attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
      setTimeout(() => this.connect(), this.reconnectDelay);
    } else {
      console.error('Max reconnect attempts reached');
    }
  }

  subscribe(listener: (status: AgentStatus) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.listeners = [];
  }

  send(data: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not open, cannot send message');
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
let wsService: WebSocketService | null = null;

export const getWebSocketService = (): WebSocketService => {
  if (!wsService) {
    // Use the backend WebSocket endpoint
    const wsUrl = process.env.REACT_APP_WS_URL || `ws://localhost:8000/ws/agent-status`;
    wsService = new WebSocketService(wsUrl);
  }
  return wsService;
};
