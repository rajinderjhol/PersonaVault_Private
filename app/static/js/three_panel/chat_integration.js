/**
 * Chat Integration - Full chat experience with thermodynamic context
 */

class ChatIntegration {
    constructor() {
        this.messages = [];
        this.currentStream = null;
        this.provider = 'groq';
        this.showThoughtProcess = false;
        this.sessionId = null;
        this.init();
    }

    init() {
        console.log("ChatIntegration: initializing...");
        this.loadChatHistory();
        this.loadProviders();
        this.setupEventListeners();
        this.loadSuggestedActions();
        console.log("ChatIntegration: initialized.");
    }

    async loadProviders() {
        const select = document.getElementById('provider-select');
        if (!select) return;

        try {
            const response = await fetch('/api/v1/ollama/models', { credentials: 'include' });
            const data = await response.json();
            select.innerHTML = '';
            
            const providers = ['groq', 'gemini'];
            providers.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
                select.appendChild(opt);
            });
            
            data.models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.model_name;
                opt.textContent = `${m.provider_type}: ${m.model_name}`;
                select.appendChild(opt);
            });
        } catch (error) {
            console.error('Failed to load providers:', error);
            select.innerHTML = '<option value="ollama">Ollama (Default)</option>';
        }
    }

    async loadChatHistory() {
        try {
            // Use the correct chat sessions endpoint
            const response = await fetch('/api/v1/chat/sessions/', { credentials: 'include' });
            if (response.ok) {
                const sessions = await response.json();
                this.sessions = sessions || [];
                
                // Render sessions in sidebar
                this.renderSessions();
                
                // Load first session if exists
                if (this.sessions.length > 0) {
                    await this.loadSession(this.sessions[0].id);
                } else {
                    this.renderMessages();
                }
            } else {
                console.warn('Failed to load sessions, status:', response.status);
                this.sessions = [];
                this.renderMessages();
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
            this.sessions = [];
            this.renderMessages();
        }
    }

    renderSessions() {
        const container = document.getElementById('session-list');
        if (!container) return;
        
        if (!this.sessions || this.sessions.length === 0) {
            container.innerHTML = `
                <div class="session-empty">
                    <span>No sessions yet</span>
                    <button onclick="chatIntegration.newChat()">+ New Chat</button>
                </div>
            `;
            return;
        }
        
        container.innerHTML = this.sessions.map(s => `
            <div class="session-item ${s.id === this.sessionId ? 'active' : ''}" 
                 onclick="chatIntegration.loadSession(${s.id})">
                <span class="session-title">${s.title || 'Untitled'}</span>
            </div>
        `).join('');
    }

    async loadSession(sessionId) {
        this.sessionId = sessionId;
        this.messages = [];
        try {
            const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, { credentials: 'include' });
            if (response.ok) {
                const data = await response.json();
                this.messages = data.messages || [];
                this.renderMessages();
            }
        } catch (error) {
            console.warn('Failed to load session messages:', error);
        }
    }

    renderMessages() {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        if (this.messages.length === 0) {
            container.innerHTML = `
                <div class="chat-empty">
                    <div class="empty-icon">👋</div>
                    <h3>Welcome to PersonaVault!</h3>
                    <p>Create a new chat session to get started.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.messages.map(msg => `
            <div class="message ${msg.role}">
                <div class="message-content">${msg.content}</div>
                ${msg.trace ? this.renderTrace(msg.trace) : ''}
                ${msg.attribution ? this.renderAttribution(msg.attribution) : ''}
            </div>
        `).join('');

        container.scrollTop = container.scrollHeight;
    }

    renderTrace(trace) {
        if (!trace || !Array.isArray(trace)) return '';
        return `
            <div class="message-trace" onclick="chatIntegration.toggleTrace('${Date.now()}')">
                <span class="trace-toggle">▶</span>
                <span class="trace-label">Decision Trace</span>
            </div>
            <div class="trace-details" id="trace-${Date.now()}" style="display:none;">
                ${trace.map(step => `
                    <div class="trace-step">
                        <span class="step-icon">✅</span>
                        <span class="step-label">${step.label || step.title || 'Step'}</span>
                        <span class="step-status">${step.description || step.summary || ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderAttribution(attribution) {
        const icons = {
            gas: '💨',
            liquid: '💧',
            ice: '🧊',
            snowflake: '❄️'
        };
        return `
            <div class="message-attribution">
                <span class="attribution-icon">${icons[attribution.phase] || '🧊'}</span>
                <span class="attribution-text">${attribution.phase} memory applied</span>
                ${attribution.pattern ? `<span class="attribution-pattern">${attribution.pattern}</span>` : ''}
            </div>
        `;
    }

    toggleTrace(traceId) {
        const container = document.getElementById(`trace-${traceId}`);
        if (container) {
            const isVisible = container.style.display === 'block';
            container.style.display = isVisible ? 'none' : 'block';
            const toggle = container.parentElement.querySelector('.trace-toggle');
            if (toggle) toggle.textContent = isVisible ? '▶' : '▼';
        }
    }

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input?.value?.trim();
        if (!message) return;

        this.addMessage('user', message);
        input.value = '';
        this.showTyping();

        try {
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: message, provider: this.provider, stream: true }),
                credentials: 'include'
            });

            if (response.ok) {
                await this.handleStream(response);
            } else {
                this.addMessage('assistant', `❌ Error occurred.`);
            }
        } catch (error) {
            this.addMessage('assistant', `❌ Error: ${error.message}`);
        } finally {
            this.hideTyping();
        }
    }

    async handleStream(response) {
        try {
            const data = await response.json();
            this.hideTyping();
            
            if (data.finalResponse) {
                // Strip <think> blocks (case-insensitive, multi-line)
                let cleanedResponse = data.finalResponse.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
                
                // Use cleanedResponse for content, reasoningTrace for the decision trace
                this.addMessage('assistant', cleanedResponse, data.reasoningTrace, data.attribution);
            } else if (data.error) {
                this.addMessage('assistant', `❌ Error: ${data.error}`);
            }
            
            document.dispatchEvent(new CustomEvent('chat-update'));
        } catch (error) {
            console.error('Failed to parse chat response:', error);
            this.hideTyping();
            this.addMessage('assistant', "❌ Failed to parse response from server.");
        }
    }

    addMessage(role, content, trace = null, attribution = null) {
        this.messages.push({ role, content, trace, attribution });
        this.renderMessages();
    }

    showTyping() {
        const container = document.getElementById('chat-messages');
        if (!container) return;
        this.typingElement = document.createElement('div');
        this.typingElement.className = 'message assistant typing';
        this.typingElement.innerHTML = `<div class="message-content"><span class="typing-dot">●</span><span class="typing-dot">●</span><span class="typing-dot">●</span></div>`;
        container.appendChild(this.typingElement);
    }

    hideTyping() {
        if (this.typingElement) {
            this.typingElement.remove();
            this.typingElement = null;
        }
    }

    setupEventListeners() {
        document.getElementById('send-btn')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('chat-input')?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); this.sendMessage(); }
        });
    }

    newChat() {
        this.messages = [];
        this.sessionId = null;
        this.renderMessages();
        const input = document.getElementById('chat-input');
        if (input) setTimeout(() => input.focus(), 100);
        document.dispatchEvent(new CustomEvent('chat-update', { detail: { reset: true } }));
        console.log('✨ New chat session created');
    }

    loadSuggestedActions() {
        // Placeholder
    }
}

window.chatIntegration = new ChatIntegration();
