/**
 * PersonaVault v2 Dashboard - Single Combined JavaScript
 */

(function() {
    'use strict';

    console.log('🛡️ PersonaVault v2 Dashboard loaded');

    // ---------- DASHBOARD ----------
    window.toggleSidebar = function() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
        }
    };

    window.closeSidebarEditor = function() {
        const editor = document.getElementById('sidebar-editor');
        if (editor) {
            editor.style.display = 'none';
        }
    };

    // ---------- SIDEBAR ----------
    class SidebarManager {
        constructor() {
            console.log('SidebarManager: initializing...');
            this.elements = [
                { id: 'dashboard', icon: '📊', label: 'Dashboard', url: '/admin/dashboard/v2' },
                { id: 'chat', icon: '💬', label: 'Chat', url: '/admin/dashboard/v2?tab=chat' },
                { id: 'swarm', icon: '🐝', label: 'Swarm', url: '/admin/swarm' },
                { id: 'compliance', icon: '⚖️', label: 'Compliance', url: '/admin/compliance' },
                { id: 'security', icon: '🔒', label: 'Security', url: '/admin/security' }
            ];
            this.render();
            console.log('SidebarManager: initialized.');
        }

        render() {
            const container = document.getElementById('sidebar-nav');
            if (!container) return;
            container.innerHTML = this.elements.map(el => `
                <a href="${el.url}" class="nav-item">
                    <span class="nav-icon">${el.icon}</span>
                    <span class="nav-label">${el.label}</span>
                </a>
            `).join('');
        }

        addElement(type, label) {
            const id = `${type}-${label.toLowerCase()}`;
            if (this.elements.some(el => el.id === id)) return;
            this.elements.push({ id, icon: '📌', label, url: '#' });
            this.render();
            if (window.closeSidebarEditor) window.closeSidebarEditor();
        }
    }

    // ---------- CONTEXT ----------
    class ContextPanel {
        constructor() {
            console.log('ContextPanel: initializing...');
            this.loadData();
        }

        async loadData() {
            try {
                const response = await fetch('/api/v1/thermodynamics/phase-distribution', {
                    credentials: 'include'
                });
                if (response.ok) {
                    const data = await response.json();
                    this.renderPhases(data);
                }
            } catch (e) {
                console.error('Failed to load phase data:', e);
            }
        }

        renderPhases(data) {
            const container = document.getElementById('thermo-distribution');
            if (!container) return;
            const total = (data.gas || 0) + (data.liquid || 0) + (data.ice || 0) + (data.snowflakes || 0) || 1;
            const phases = [
                { id: 'gas', count: data.gas || 0, label: 'Gas', icon: '💨' },
                { id: 'liquid', count: data.liquid || 0, label: 'Liquid', icon: '💧' },
                { id: 'ice', count: data.ice || 0, label: 'Ice', icon: '🧊' },
                { id: 'snowflake', count: data.snowflakes || 0, label: 'Snowflakes', icon: '❄️' }
            ];
            container.innerHTML = `<div class="phase-bars">${phases.map(p => `
                <div class="phase-bar ${p.id}">
                    <span class="phase-icon">${p.icon}</span>
                    <span class="phase-label">${p.label}</span>
                    <span class="phase-count">${p.count}</span>
                    <div class="phase-track">
                        <div class="phase-fill" style="width: ${Math.max((p.count / total) * 100, 0.5)}%"></div>
                    </div>
                </div>
            `).join('')}</div>`;
        }
    }

    // ---------- CHAT ----------
    class ChatIntegration {
        constructor() {
            console.log('ChatIntegration: initializing...');
            this.messages = [];
            this.sessionId = null;
            this.setupEventListeners();
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
                    credentials: 'include',
                    body: JSON.stringify({ query: message })
                });
                if (response.ok) {
                    const data = await response.json();
                    this.hideTyping();
                    this.addMessage('assistant', data.response || 'No response');
                } else {
                    this.hideTyping();
                    this.addMessage('assistant', '❌ Error occurred.');
                }
            } catch (error) {
                this.hideTyping();
                this.addMessage('assistant', `❌ Error: ${error.message}`);
            }
        }

        addMessage(role, content) {
            const container = document.getElementById('chat-messages');
            if (!container) return;
            const msg = document.createElement('div');
            msg.className = `message ${role}`;
            msg.innerHTML = `<div class="message-content">${content}</div>`;
            container.appendChild(msg);
            container.scrollTop = container.scrollHeight;
        }

        showTyping() {
            const container = document.getElementById('chat-messages');
            if (!container) return;
            this.typingElement = document.createElement('div');
            this.typingElement.className = 'message assistant typing';
            this.typingElement.innerHTML = `<div class="message-content">⏳ Thinking...</div>`;
            container.appendChild(this.typingElement);
            container.scrollTop = container.scrollHeight;
        }

        hideTyping() {
            if (this.typingElement) {
                this.typingElement.remove();
                this.typingElement = null;
            }
        }

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
        }

        newChat() {
            const container = document.getElementById('chat-messages');
            if (container) {
                container.innerHTML = `
                    <div class="chat-empty">
                        <div class="empty-icon">👋</div>
                        <h3>Welcome to PersonaVault!</h3>
                        <p>Start a new conversation to begin.</p>
                    </div>
                `;
            }
            this.messages = [];
        }
    }

    // ---------- INITIALIZE ----------
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🎯 Initializing components...');
        window.sidebarManager = new SidebarManager();
        window.contextPanel = new ContextPanel();
        window.chatIntegration = new ChatIntegration();
        console.log('✅ All components initialized.');
    });

})();
