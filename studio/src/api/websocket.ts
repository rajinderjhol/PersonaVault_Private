/**
 * WebSocket Client for Real-Time Intelligence Stream
 * Connects to the backend WebSocket endpoint for live agent reasoning
 */

export interface ThoughtStep {
  step: number;
  label: string;
  description: string;
  status: 'pending' | 'in_progress' | 'complete';
  timestamp: string;
}

export interface WebSocketMessage {
  type: 'thought' | 'trace' | 'decision' | 'phase_transition' | 'error';
  data: ThoughtStep | any;
}

export class IntelligenceWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: ((msg: WebSocketMessage) => void)[] = [];
  private isConnected = false;

  constructor(private url: string) {}

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('🧠 WebSocket: Connected to intelligence stream');
        this.isConnected = true;
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('WebSocket: Failed to parse message', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket: Disconnected');
        this.isConnected = false;
        this.attemptReconnect();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket: Error', error);
      };
    } catch (error) {
      console.error('WebSocket: Failed to connect', error);
      this.attemptReconnect();
    }
  }

  private handleMessage(data: any): void {
    const message: WebSocketMessage = {
      type: data.type || 'thought',
      data: data.data || data,
    };
    this.messageHandlers.forEach((handler) => handler(message));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('WebSocket: Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(`WebSocket: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      if (!this.isConnected) {
        this.connect();
      }
    }, delay);
  }

  onMessage(handler: (msg: WebSocketMessage) => void): void {
    this.messageHandlers.push(handler);
  }

  send(message: any): void {
    if (this.ws && this.isConnected) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket: Cannot send, not connected');
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  isConnectedState(): boolean {
    return this.isConnected;
  }
}
