/**
 * Trace Chat - Enhanced chat with decision trace support
 */

class TraceChat {
    constructor(options = {}) {
        this.chatContainer = options.chatContainer || '#chat-container';
        this.traceSidebar = options.traceSidebar || '#trace-sidebar';
        this.messageInput = options.messageInput || '#chat-input';
        this.sendButton = options.sendButton || '#send-button';
        this.traces = {};
        this.currentDecisionId = null;
        
        this.init();
    }
    
    init() {
        // Bind events
        document.querySelector(this.sendButton).addEventListener('click', () => this.sendMessage());
        document.querySelector(this.messageInput).addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Setup WebSocket for streaming
        this.setupWebSocket();
        
        console.log('TraceChat initialized');
    }
    
    setupWebSocket() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/admin/dashboard/ws/chat`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };
        
        this.ws.onopen = () => {
            console.log('✅ TraceChat WebSocket connected');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'content':
                this.appendContent(data.data);
                break;
            case 'thought':
                this.appendThought(data.data);
                break;
            case 'decision_id':
                this.setCurrentDecisionId(data.data);
                break;
            case 'trace':
                this.displayTrace(data.data);
                break;
            case 'done':
                this.onStreamComplete();
                break;
            case 'error':
                this.showError(data.data.error);
                break;
        }
    }
    
    sendMessage() {
        const input = document.querySelector(this.messageInput);
        const message = input.value.trim();
        if (!message) return;
        
        // Clear input
        input.value = '';
        
        // Add user message to chat
        this.addMessage(message, 'user');
        
        // Show loading indicator
        this.showLoading();
        
        // Send through WebSocket
        this.ws.send(JSON.stringify({
            type: 'chat',
            query: message,
            provider: 'groq'
        }));
    }
    
    addMessage(content, role) {
        const container = document.querySelector(this.chatContainer);
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        // Message content
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (role === 'assistant') {
            // Add trace toggle button
            contentDiv.innerHTML = `
                <p>${this.formatContent(content)}</p>
                <button class="btn btn-outline-primary btn-sm toggle-trace-btn" 
                        onclick="traceChat.toggleTrace(event, this)">
                    📋 View Decision Trace
                </button>
                <div class="trace-collapse collapse" id="trace-${Date.now()}">
                    <div class="card card-body">
                        <div class="trace-loading"></div>
                        <small>Loading trace...</small>
                    </div>
                </div>
            `;
        } else {
            contentDiv.innerHTML = `<p>${this.formatContent(content)}</p>`;
        }
        
        messageDiv.appendChild(contentDiv);
        container.appendChild(messageDiv);
        
        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
        
        return messageDiv;
    }
    
    appendContent(chunk) {
        // Find the last assistant message or create one
        let lastMessage = document.querySelector('.chat-message.assistant-message:last-child');
        if (!lastMessage || lastMessage.dataset.complete === 'true') {
            lastMessage = this.addMessage('', 'assistant');
            lastMessage.dataset.complete = 'false';
        }
        
        // Append chunk to content
        const contentP = lastMessage.querySelector('.message-content p');
        if (contentP) {
            contentP.textContent += chunk;
        }
    }
    
    appendThought(thought) {
        // Thought handling logic
        console.log("Thought:", thought);
    }
    
    formatContent(content) {
        // Basic markdown-like formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }
    
    setCurrentDecisionId(decisionId) {
        this.currentDecisionId = decisionId;
        
        // Update the trace sidebar
        this.loadTrace(decisionId);
    }
    
    async loadTrace(decisionId) {
        const sidebar = document.querySelector(this.traceSidebar);
        sidebar.innerHTML = `
            <h6>🛡️ DECISION TRACE</h6>
            <div class="trace-loading"></div>
            <small>Loading trace ${decisionId}...</small>
        `;
        
        try {
            const response = await fetch(`/api/v1/decisions/${decisionId}/trace`);
            if (!response.ok) throw new Error('Trace not found');
            
            const data = await response.json();
            this.displayTrace(data);
            this.traces[decisionId] = data;
            
        } catch (error) {
            sidebar.innerHTML = `
                <h6>🛡️ DECISION TRACE</h6>
                <div class="text-danger">Error loading trace: ${error.message}</div>
            `;
        }
    }
    
    displayTrace(data) {
        const sidebar = document.querySelector(this.traceSidebar);
        const trace = data.trace || data;
        
        let html = `
            <h6>🛡️ DECISION TRACE</h6>
            <div class="text-muted small">${data.decision_id || 'Unknown ID'}</div>
            <hr>
        `;
        
        // Perception
        if (trace.perception) {
            html += `
                <div class="trace-step perception">
                    <div class="step-label">🔍 Perception</div>
                    <div class="step-content">${JSON.stringify(trace.perception, null, 2)}</div>
                </div>
            `;
        }
        
        // Signals
        if (trace.signals) {
            html += `
                <div class="trace-step signals">
                    <div class="step-label">📋 Signals</div>
                    <div class="step-content">${JSON.stringify(trace.signals, null, 2)}</div>
                </div>
            `;
        }
        
        // Policy
        if (trace.policy) {
            html += `
                <div class="trace-step policy">
                    <div class="step-label">⚖️ Policy</div>
                    <div class="step-content">${JSON.stringify(trace.policy, null, 2)}</div>
                </div>
            `;
        }
        
        // Decision
        if (trace.decision) {
            html += `
                <div class="trace-step decision">
                    <div class="step-label">🧠 Decision</div>
                    <div class="step-content">${JSON.stringify(trace.decision, null, 2)}</div>
                </div>
            `;
        }
        
        // Autonomy
        if (trace.autonomy) {
            html += `
                <div class="trace-step autonomy">
                    <div class="step-label">🛡️ Autonomy</div>
                    <div class="step-content">${JSON.stringify(trace.autonomy, null, 2)}</div>
                </div>
            `;
        }
        
        // Actions
        if (trace.actions) {
            html += `
                <div class="trace-step action">
                    <div class="step-label">⚡ Actions</div>
                    <div class="step-content">${JSON.stringify(trace.actions, null, 2)}</div>
                </div>
            `;
        }
        
        // Explanation
        if (data.explanation) {
            html += `
                <hr>
                <div class="small">
                    <strong>💡 Explanation</strong>
                    <div class="text-muted">${data.explanation}</div>
                </div>
            `;
        }
        
        // Metadata
        html += `
            <hr>
            <div class="small text-muted">
                <div>Pack: ${data.pack?.name || 'Unknown'} v${data.pack?.version || '1.0.0'}</div>
                <div>Latency: ${data.latency_ms || 0}ms</div>
                <div>Timestamp: ${data.timestamp || 'Unknown'}</div>
            </div>
            <div class="mt-2">
                <button class="btn btn-sm btn-outline-light" onclick="traceChat.exportTrace('${data.decision_id}')">
                    📋 Export JSON
                </button>
                <button class="btn btn-sm btn-outline-light" onclick="traceChat.verifyTrace('${data.decision_id}')">
                    ⚖️ Verify
                </button>
            </div>
        `;
        
        sidebar.innerHTML = html;
    }
    
    async exportTrace(decisionId) {
        window.open(`/api/v1/decisions/${decisionId}/export`, '_blank');
    }
    
    async verifyTrace(decisionId) {
        try {
            const response = await fetch(`/api/v1/decisions/${decisionId}/verify`);
            const result = await response.json();
            
            // Show verification result
            alert(`Verification Result:\n${JSON.stringify(result, null, 2)}`);
            
        } catch (error) {
            alert(`Verification failed: ${error.message}`);
        }
    }
    
    toggleTrace(event, button) {
        event.preventDefault();
        const collapseDiv = button.parentElement.querySelector('.trace-collapse');
        if (collapseDiv) {
            // Load trace if not loaded
            const card = collapseDiv.querySelector('.card');
            if (card && card.innerHTML.includes('Loading trace')) {
                const decisionId = this.currentDecisionId;
                if (decisionId) {
                    this.loadTraceIntoCollapse(decisionId, card);
                }
            }
            // Toggle
            const collapse = new bootstrap.Collapse(collapseDiv);
            collapse.toggle();
        }
    }
    
    async loadTraceIntoCollapse(decisionId, card) {
        try {
            const response = await fetch(`/api/v1/decisions/${decisionId}/trace`);
            if (!response.ok) throw new Error('Trace not found');
            
            const data = await response.json();
            card.innerHTML = `
                <pre>${JSON.stringify(data, null, 2)}</pre>
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-light" onclick="traceChat.exportTrace('${decisionId}')">
                        📋 Export JSON
                    </button>
                    <button class="btn btn-sm btn-outline-light" onclick="traceChat.verifyTrace('${decisionId}')">
                        ⚖️ Verify
                    </button>
                </div>
            `;
        } catch (error) {
            card.innerHTML = `<div class="text-danger">Error: ${error.message}</div>`;
        }
    }
    
    showLoading() {
        // Add a loading indicator to the chat
        const container = document.querySelector(this.chatContainer);
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message assistant-message loading';
        loadingDiv.id = 'loading-indicator';
        loadingDiv.innerHTML = `
            <div class="message-content">
                <div class="trace-loading"></div>
                <span class="text-muted">Thinking...</span>
            </div>
        `;
        container.appendChild(loadingDiv);
        container.scrollTop = container.scrollHeight;
    }
    
    hideLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) loading.remove();
    }
    
    onStreamComplete() {
        this.hideLoading();
        const lastMessage = document.querySelector('.chat-message.assistant-message:last-child');
        if (lastMessage) {
            lastMessage.dataset.complete = 'true';
        }
    }
    
    showError(message) {
        this.hideLoading();
        const container = document.querySelector(this.chatContainer);
        const errorDiv = document.createElement('div');
        errorDiv.className = 'chat-message error-message';
        errorDiv.innerHTML = `
            <div class="message-content text-danger">
                ⚠️ ${message}
            </div>
        `;
        container.appendChild(errorDiv);
        container.scrollTop = container.scrollHeight;
    }
}

// Initialize when DOM is ready
let traceChat = null;

document.addEventListener('DOMContentLoaded', function() {
    traceChat = new TraceChat({
        chatContainer: '#chat-container',
        traceSidebar: '#trace-sidebar',
        messageInput: '#chat-input',
        sendButton: '#send-button'
    });
});
