class WebSocketManager {
    constructor(options = {}) {
        this.url = options.url;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.baseDelay = options.baseDelay || 1000;
        this.maxDelay = options.maxDelay || 30000;
        this.ws = null;
        this.isConnected = false;
        this.isConnecting = false;
        this.shouldReconnect = true;
        this.reconnectTimer = null;
        this.messageHandlers = [];
        this.connectionHandlers = [];
        this.disconnectionHandlers = [];
        this.errorHandlers = [];
        
        if (this.url) {
            setTimeout(() => this.connect(), 100);
        }
    }
    
    connect() {
        if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
            return;
        }
        
        this.isConnecting = true;
        console.log(`🔌 WebSocket connecting to ${this.url}...`);
        
        try {
            const ws = new WebSocket(this.url);
            this.ws = ws;
            
            ws.onopen = (event) => {
                this.isConnected = true;
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                console.log(`✅ WebSocket connected`);
                this.connectionHandlers.forEach(h => { try { h(event); } catch(e) {} });
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.messageHandlers.forEach(h => { try { h(data, event); } catch(e) {} });
                } catch(e) {
                    this.messageHandlers.forEach(h => { try { h(event.data, event); } catch(e) {} });
                }
            };
            
            ws.onclose = (event) => {
                this.isConnected = false;
                this.isConnecting = false;
                console.log(`🔌 WebSocket closed (code: ${event.code})`);
                this.disconnectionHandlers.forEach(h => { try { h(event); } catch(e) {} });
                if (this.shouldReconnect && event.code !== 1000) {
                    this.scheduleReconnect();
                }
            };
            
            ws.onerror = (event) => {
                console.error('❌ WebSocket error:', event);
                this.errorHandlers.forEach(h => { try { h(event); } catch(e) {} });
            };
            
        } catch (error) {
            console.error('❌ WebSocket connection error:', error);
            this.isConnecting = false;
            this.scheduleReconnect();
        }
    }
    
    scheduleReconnect() {
        if (!this.shouldReconnect) return;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`❌ Max reconnect attempts (${this.maxReconnectAttempts}) reached.`);
            this.shouldReconnect = false;
            return;
        }
        this.reconnectAttempts++;
        const exponentialDelay = Math.min(
            this.baseDelay * Math.pow(2, this.reconnectAttempts - 1),
            this.maxDelay
        );
        const jitter = (Math.random() * 200) - 100;
        const delay = Math.max(100, exponentialDelay + jitter);
        console.log(`🔄 Reconnecting in ${(delay / 1000).toFixed(1)}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            if (this.shouldReconnect && !this.isConnected) {
                this.connect();
            }
        }, delay);
    }
    
    send(data) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.ws.send(message);
            return true;
        }
        console.warn('⚠️ Cannot send: WebSocket not connected');
        return false;
    }
    
    close(code = 1000, reason = 'Normal closure') {
        this.shouldReconnect = false;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            this.ws.close(code, reason);
            this.ws = null;
        }
        this.isConnected = false;
        this.isConnecting = false;
        console.log(`🔌 WebSocket closed`);
    }
    
    onMessage(handler) { this.messageHandlers.push(handler); return this; }
    onConnect(handler) { this.connectionHandlers.push(handler); return this; }
    onDisconnect(handler) { this.disconnectionHandlers.push(handler); return this; }
    onError(handler) { this.errorHandlers.push(handler); return this; }
    
    get status() {
        if (this.isConnected) return 'connected';
        if (this.isConnecting) return 'connecting';
        return 'disconnected';
    }
    
    reset() {
        this.reconnectAttempts = 0;
        this.shouldReconnect = true;
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }
}

if (typeof window !== 'undefined') {
    window.WebSocketManager = WebSocketManager;
}
