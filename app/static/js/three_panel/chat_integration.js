/**
 * Chat Integration - Full chat experience with thermodynamic context
 */

class ChatIntegration {
    constructor() {
        this.messages = [];
        this.sessions = [];
        this.sessionId = null;
        this.provider = 'groq';
        this.showThoughtProcess = false;
        this.init();
    }

    init() {
        console.log("ChatIntegration: initializing...");
        this.loadSessions();
        this.loadProviders();
        this.setupEventListeners();
        console.log("ChatIntegration: initialized.");
    }

    // --- Session Management ---

    async loadSessions() {
        try {
            const response = await fetch('/api/v1/chat/sessions/', { 
                credentials: 'include' 
            });
            if (response.ok) {
                const data = await response.json();
                this.sessions = data.sessions || [];
                this.renderSessions();
                
                if (this.sessions.length > 0) {
                    await this.loadSession(this.sessions[0].id);
                } else {
                    this.createNewSession();
                }
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
            this.createNewSession();
        }
    }

    renderSessions() {
        const container = document.getElementById('session-list');
        if (!container) return;

        if (!this.sessions || this.sessions.length === 0) {
            container.innerHTML = `
                <div class="session-empty">No sessions yet</div>
            `;
            return;
        }

        container.innerHTML = this.sessions.map(s => `
            <div class="session-item ${s.id === this.sessionId ? 'active' : ''}" 
                 onclick="chatIntegration.loadSession(${s.id})">
                <span class="session-title">${s.title || 'New Chat'}</span>
                <span class="session-time">${s.updated_at ? new Date(s.updated_at).toLocaleDateString() : ''}</span>
                <span class="session-count">${s.message_count || 0}</span>
            </div>
        `).join('');
    }

    async createNewSession() {
        try {
            const response = await fetch('/api/v1/chat/sessions/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ title: 'New Chat' })
            });
            if (response.ok) {
                const data = await response.json();
                this.sessions.unshift(data);
                this.sessionId = data.id;
                this.messages = [];
                this.renderSessions();
                this.renderMessages();
                console.log('✨ New chat session created:', data.id);
            }
        } catch (error) {
            console.error('Failed to create session:', error);
            // Fallback: local session
            this.sessionId = Date.now();
            this.messages = [];
            this.renderMessages();
        }
    }

    async loadSession(sessionId) {
        this.sessionId = sessionId;
        try {
            const response = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`, {
                credentials: 'include'
            });
            if (response.ok) {
                const data = await response.json();
                this.messages = data.messages || [];
                this.renderMessages();
                this.renderSessions();
                console.log('📚 Loaded session:', sessionId, 'with', this.messages.length, 'messages');
            }
        } catch (error) {
            console.error('Failed to load session:', error);
            this.messages = [];
            this.renderMessages();
        }
    }

    // --- Provider Management ---

    async loadProviders() {
        const select = document.getElementById('provider-select');
        if (!select) return;

        try {
            const response = await fetch('/api/v1/ollama/models', { credentials: 'include' });
            const data = await response.json();
            
            select.innerHTML = '';
            
            // Add other providers
            const providers = ['groq', 'gemini'];
            providers.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p;
                opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
                select.appendChild(opt);
            });
            
            // Add dynamic models
            if (data.models) {
                data.models.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.model_name || m;
                    opt.textContent = `Ollama: ${m.model_name || m}`;
                    select.appendChild(opt);
                });
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
            select.innerHTML = '<option value="groq">Groq</option><option value="ollama">Ollama</option>';
        }
    }

    // --- Message Rendering ---

    renderMessages() {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        if (this.messages.length === 0) {
            container.innerHTML = `
                <div class="chat-empty">
                    <div class="empty-icon">👋</div>
                    <h3>Welcome to PersonaVault!</h3>
                    <p>Start a new conversation to begin.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.messages.map(msg => {
            let content = this.renderMarkdown(msg.content);
            return `
                <div class="message ${msg.role}">
                    <div class="message-content">${content}</div>
                    ${msg.trace ? this.renderTrace(msg.trace) : ''}
                    ${msg.attribution ? this.renderAttribution(msg.attribution) : ''}
                </div>
            `;
        }).join('');

        container.scrollTop = container.scrollHeight;
    }

    renderMarkdown(text) {
        if (!text) return '';
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
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
                        <span class="step-status">${step.summary || step.description || ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderAttribution(attribution) {
        const icons = { gas: '💨', liquid: '💧', ice: '🧊', snowflake: '❄️' };
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

    // --- Message Sending ---

    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input?.value?.trim();
        if (!message) return;

        // If no session, create one
        if (!this.sessionId) {
            await this.createNewSession();
        }

        this.addMessage('user', message);
        input.value = '';
        this.showTyping();

        try {
            const response = await fetch('/api/v1/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ 
                    query: message, 
                    session_id: this.sessionId,
                    provider: this.provider,
                    stream: true 
                })
            });

            if (response.ok) {
                await this.handleStream(response);
                await this.loadSessions(); // Refresh session list
            } else {
                this.addMessage('assistant', '❌ Error occurred.');
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
                let cleanedResponse = data.finalResponse.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
                this.addMessage('assistant', cleanedResponse, data.reasoningTrace, data.attribution);
            } else if (data.error) {
                this.addMessage('assistant', `❌ Error: ${data.error}`);
            } else if (data.response) {
                this.addMessage('assistant', data.response);
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
        this.typingElement.innerHTML = `
            <div class="message-content">
                <span class="typing-dot">●</span>
                <span class="typing-dot">●</span>
                <span class="typing-dot">●</span>
            </div>
        `;
        container.appendChild(this.typingElement);
        container.scrollTop = container.scrollHeight;
    }

    hideTyping() {
        if (this.typingElement) {
            this.typingElement.remove();
            this.typingElement = null;
        }
    }

    // --- Event Listeners ---

    setupEventListeners() {
        const sendBtn = document.getElementById('send-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendMessage());
        }

        const input = document.getElementById('chat-input');
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }

        const providerSelect = document.getElementById('provider-select');
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                this.provider = e.target.value;
            });
        }

        const thoughtToggle = document.getElementById('thought-toggle');
        if (thoughtToggle) {
            thoughtToggle.addEventListener('change', (e) => {
                this.showThoughtProcess = e.target.checked;
            });
        }
    }
}

// Initialize
window.chatIntegration = new ChatIntegration();
