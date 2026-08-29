/**
 * Premium Chat Experience - PersonaVault
 * Streaming, rich formatting, real-time feedback
 */

class PremiumChat {
    constructor() {
        this.container = document.getElementById('chat-container');
        this.messages = [];
        this.isStreaming = false;
        this.currentStream = null;
        this.init();
    }
    
    init() {
        if (!this.container) return;
        this.render();
        this.setupEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="chat-premium">
                <!-- Header -->
                <div class="chat-header">
                    <div class="brand">
                        <span class="icon">🧠</span>
                        <div>
                            <span class="name">PersonaVault</span>
                            <span class="tagline">Sovereign Intelligence Platform</span>
                        </div>
                    </div>
                    <div class="header-actions">
                        <button class="header-btn" onclick="premiumChat.newSession()">➕ New</button>
                        <button class="header-btn" onclick="premiumChat.toggleContext()">📊 Context</button>
                        <button class="header-btn" onclick="premiumChat.clearChat()">🗑️ Clear</button>
                    </div>
                </div>
                
                <!-- Context Panel (Collapsible) -->
                <div class="context-panel" id="context-panel">
                    <div class="context-grid">
                        <div class="context-item">
                            <span class="label">🧠 Memory</span>
                            <span class="value">💨 Active</span>
                        </div>
                        <div class="context-item">
                            <span class="label">🐝 Swarm</span>
                            <span class="value" id="swarm-status">Idle</span>
                        </div>
                        <div class="context-item">
                            <span class="label">🔒 Sovereignty</span>
                            <span class="value">✅ Air-gap Ready</span>
                        </div>
                    </div>
                </div>
                
                <!-- Messages -->
                <div class="messages-container" id="messages-container">
                    <div class="welcome-message">
                        <div class="welcome-icon">🧠</div>
                        <h2>Welcome to PersonaVault</h2>
                        <p>Your Sovereign Intelligence Platform. Ask me anything.</p>
                        <div class="quick-start-chips">
                            <button class="chip" onclick="premiumChat.sendQuickQuery('Analyze this security policy...')">🔒 Security Analysis</button>
                            <button class="chip" onclick="premiumChat.sendQuickQuery('Tell me about my memories')">🧠 View Memories</button>
                        </div>
                    </div>
                </div>
                
                <!-- Status Bar -->
                <div class="status-bar" id="status-bar">
                    <span class="status-dot ready"></span>
                    <span class="status-text" id="status-text">🟢 Ready</span>
                </div>
                
                <!-- Input Area -->
                <div class="input-area">
                    <div class="input-wrapper">
                        <textarea 
                            id="chat-input" 
                            rows="1" 
                            placeholder="Ask me anything..."
                            onkeydown="premiumChat.handleKeyDown(event)"
                        ></textarea>
                        <button class="send-btn" id="send-btn" onclick="premiumChat.sendMessage()">
                            Send ✨
                        </button>
                    </div>
                </div>
            </div>
        `;
    }
    
    setupEventListeners() {
        const input = document.getElementById('chat-input');
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const query = input.value.trim();
        if (!query || this.isStreaming) return;
        
        input.value = '';
        input.style.height = 'auto';
        
        this.addMessage('user', query);
        this.setStatus('🧠 Thinking...', 'thinking');
        this.isStreaming = true;
        document.getElementById('send-btn').disabled = true;
        
        try {
            const response = await fetch('/api/v1/chat/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, user_id: 1 })
            });
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            
            let messageId = this.addMessage('assistant', '');
            let content = '';
            
            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value);
                const lines = chunk.split('\n').filter(line => line.trim());
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === 'status') {
                            this.setStatus(data.message, 'processing');
                        } else if (data.type === 'content') {
                            content += data.content;
                            this.updateMessageContent(messageId, content);
                        } else if (data.type === 'done') {
                            this.setStatus('✅ Complete', 'ready');
                        }
                    }
                }
            }
        } catch (error) {
            this.setStatus('❌ Error: ' + error.message, 'error');
        }
        
        this.isStreaming = false;
        document.getElementById('send-btn').disabled = false;
    }
    
    addMessage(role, content) {
        const container = document.getElementById('messages-container');
        const welcome = container.querySelector('.welcome-message');
        if (welcome) welcome.remove();
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        messageDiv.id = `msg-${Date.now()}`;
        
        messageDiv.innerHTML = `
            <div class="avatar">${role === 'user' ? '👤' : '🤖'}</div>
            <div class="content">
                <div class="bubble">
                    <div class="text" id="text-${messageDiv.id}">${content || '...'}</div>
                </div>
            </div>
        `;
        container.appendChild(messageDiv);
        this.scrollToBottom();
        return messageDiv.id;
    }
    
    updateMessageContent(messageId, content) {
        const textEl = document.getElementById(`text-${messageId}`);
        if (textEl) {
            textEl.textContent = content;
            this.scrollToBottom();
        }
    }
    
    setStatus(message, type) {
        const statusText = document.getElementById('status-text');
        const statusDot = document.querySelector('.status-dot');
        if (statusText) statusText.textContent = message;
        if (statusDot) statusDot.className = `status-dot ${type}`;
    }
    
    scrollToBottom() {
        const container = document.getElementById('messages-container');
        container.scrollTop = container.scrollHeight;
    }
    
    handleKeyDown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    newSession() {
        const container = document.getElementById('messages-container');
        container.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">🧠</div>
                <h2>New Session</h2>
            </div>
        `;
        this.setStatus('🟢 Ready', 'ready');
    }
    
    toggleContext() {
        const panel = document.getElementById('context-panel');
        panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
    }
    
    clearChat() {
        this.newSession();
    }
    
    sendQuickQuery(query) {
        document.getElementById('chat-input').value = query;
        this.sendMessage();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.premiumChat = new PremiumChat();
});


/**
 * Proactive Suggestions - Display and manage suggestions
 */

class ProactiveSuggestions {
    constructor() {
        this.suggestions = [];
        this.container = document.getElementById('suggestions-container');
        this.dismissed = new Set();
        this.init();
    }
    
    init() {
        if (!this.container) return;
        this.loadSuggestions();
        this.startPolling();
    }
    
    async loadSuggestions() {
        try {
            const user_id = 1; // TODO: Get from session
            const response = await fetch(`/api/v1/proactive/suggestions/${user_id}`);
            const data = await response.json();
            
            // Filter out dismissed
            this.suggestions = data.suggestions.filter(
                s => !this.dismissed.has(s.id)
            );
            
            this.render();
        } catch (error) {
            console.debug('Failed to load suggestions:', error);
        }
    }
    
    render() {
        if (!this.container) return;
        
        if (this.suggestions.length === 0) {
            this.container.innerHTML = `
                <div class="suggestions-placeholder">
                    <span>💡 No suggestions right now</span>
                </div>
            `;
            return;
        }
        
        this.container.innerHTML = `
            <div class="suggestions-header">
                <span>💡 Proactive Suggestions</span>
                <button onclick="proactiveSuggestions.dismissAll()">✕</button>
            </div>
            <div class="suggestions-list">
                ${this.suggestions.map(s => `
                    <div class="suggestion-item" data-id="${s.id}">
                        <div class="suggestion-content">
                            <div class="suggestion-title">
                                <span class="suggestion-type">${this.getTypeIcon(s.type)}</span>
                                ${s.title}
                            </div>
                            <div class="suggestion-description">${s.description}</div>
                            <div class="suggestion-actions">
                                <button class="suggestion-execute" onclick="proactiveSuggestions.execute('${s.id}')">
                                    ▶️ ${this.getActionLabel(s.action)}
                                </button>
                                <button class="suggestion-dismiss" onclick="proactiveSuggestions.dismiss('${s.id}')">
                                    ✕
                                </button>
                            </div>
                        </div>
                        <div class="suggestion-confidence">
                            ${Math.round(s.confidence * 100)}%
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    getTypeIcon(type) {
        const icons = {
            'memory': '🧠',
            'time': '⏰',
            'context': '📋',
            'action': '⚡'
        };
        return icons[type] || '💡';
    }
    
    getActionLabel(action) {
        const labels = {
            'onboarding': 'Get Started',
            'revisit_pattern': 'Review',
            'show_related': 'View Related',
            'save_to_memory': 'Save',
            'schedule': 'Schedule',
            'set_reminder': 'Remind Me',
            'execute_workflow': 'Execute',
            'show_events': 'View Events',
            'show_tasks': 'View Tasks'
        };
        return labels[action?.type] || 'Act';
    }
    
    async dismiss(suggestionId) {
        this.dismissed.add(suggestionId);
        
        try {
            const user_id = 1;
            await fetch(`/api/v1/proactive/suggestions/${suggestionId}/dismiss?user_id=${user_id}`, {
                method: 'POST'
            });
        } catch (error) {
            console.debug('Failed to dismiss:', error);
        }
        
        this.loadSuggestions();
    }
    
    dismissAll() {
        this.suggestions.forEach(s => this.dismissed.add(s.id));
        this.loadSuggestions();
    }
    
    async execute(suggestionId) {
        const suggestion = this.suggestions.find(s => s.id === suggestionId);
        if (!suggestion) return;
        
        try {
            const user_id = 1;
            const response = await fetch(`/api/v1/proactive/suggestions/${suggestionId}/execute?user_id=${user_id}`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.dismiss(suggestionId);
                
                // Show success message in chat
                const chat = window.premiumChat;
                if (chat) {
                    chat.addMessage('assistant', `✅ ${suggestion.title} completed!`);
                }
            }
        } catch (error) {
            console.error('Failed to execute:', error);
        }
    }
    
    startPolling() {
        // Refresh suggestions every 30 seconds
        setInterval(() => {
            this.loadSuggestions();
        }, 30000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.proactiveSuggestions = new ProactiveSuggestions();
});
