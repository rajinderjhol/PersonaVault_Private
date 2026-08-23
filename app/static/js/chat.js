// ============================================================
// CHAT FUNCTIONS - Complete chat UI with Provider Management
// ============================================================

// ============ CONFIGURATION ============
let autoScroll = true;
const MAX_MESSAGE_LENGTH = 2000;
let currentSessionId = null;
let thoughtSteps = [];
let thoughtTimer = null;
let thoughtStartTime = null;
let cachedPrimaryProvider = null;

// ============ FETCH HELPER ============
function getFetchOptions(method = 'GET', body = null) {
    const options = {
        method: method,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json'
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    return options;
}

// ============ MARKDOWN CONFIGURATION ============
if (typeof marked === 'undefined') {
    console.warn('⚠️ Marked library not loaded - using plain text fallback');
}

const markdownConfig = {
    gfm: true,
    breaks: true,
    headerIds: false,
    mangle: false,
    highlight: function(code, lang) {
        if (lang && typeof hljs !== 'undefined' && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (e) {
                return code;
            }
        }
        try {
            if (typeof hljs !== 'undefined') {
                return hljs.highlightAuto(code).value;
            }
        } catch (e) {
            return code;
        }
        return code;
    }
};

if (typeof marked !== 'undefined') {
    marked.setOptions(markdownConfig);
    console.log('✅ Markdown configured');
}

// ============ PROVIDER MANAGEMENT ============
async function getPrimaryProvider() {
    try {
        const response = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider', {
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            const data = await response.json();
            const provider = data.primary_provider || 'ollama';
            cachedPrimaryProvider = provider;
            console.log('📡 Primary provider from server:', provider);
            return provider;
        }
    } catch (e) {
        console.warn('Failed to fetch primary provider:', e);
    }
    return 'ollama';
}

async function loadProviderIntoUI() {
    const provider = await getPrimaryProvider();
    
    // Update context bar
    const contextEl = document.getElementById('context-provider');
    if (contextEl) contextEl.textContent = provider;
    
    // Update dropdown
    const select = document.getElementById('chat-provider');
    if (select) {
        // Add the provider if not exists
        let optionExists = false;
        for (let i = 0; i < select.options.length; i++) {
            if (select.options[i].value === provider) {
                optionExists = true;
                break;
            }
        }
        if (!optionExists) {
            const option = document.createElement('option');
            option.value = provider;
            option.textContent = provider.charAt(0).toUpperCase() + provider.slice(1);
            select.appendChild(option);
        }
        select.value = provider;
        
        // Add change listener for UI feedback
        select.addEventListener('change', (e) => {
            const newProvider = e.target.value;
            const contextEl = document.getElementById('context-provider');
            if (contextEl) contextEl.textContent = newProvider;
            showToast(`🚀 Switched AI provider to: ${newProvider.toUpperCase()}`, 'success');
        });
    }
    
    return provider;
}

// ============ TOAST NOTIFICATIONS ============
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 8px;
        `;
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.style.cssText = `
        padding: 12px 20px;
        border-radius: 8px;
        background: ${type === 'error' ? '#991b1b' : type === 'success' ? '#14532d' : '#1e293b'};
        color: #f1f5f9;
        border: 1px solid ${type === 'error' ? '#f87171' : type === 'success' ? '#22c55e' : '#334155'};
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        animation: slideIn 0.3s ease;
        min-width: 200px;
        font-size: 14px;
    `;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ THOUGHT PROCESS UI ============
function toggleThoughtProcess() {
    const container = document.getElementById('thought-process-container');
    const toggleBtn = document.querySelector('[onclick="toggleThoughtProcess()"]');
    
    if (!container) {
        const chatContainer = document.getElementById('chat-container') || document.body;
        const newContainer = document.createElement('div');
        newContainer.id = 'thought-process-container';
        newContainer.style.cssText = 'margin-top: 10px; display: block;';
        
        const thoughtProcess = document.createElement('div');
        thoughtProcess.id = 'thought-process';
        thoughtProcess.style.cssText = 'max-height: 200px; overflow-y: auto; padding: 8px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 12px; color: #94a3b8;';
        newContainer.appendChild(thoughtProcess);
        
        const statusEl = document.createElement('div');
        statusEl.id = 'thought-status';
        statusEl.style.cssText = 'font-size: 11px; color: #64748b; margin-top: 4px;';
        newContainer.appendChild(statusEl);
        
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages && chatMessages.parentElement) {
            chatMessages.parentElement.insertBefore(newContainer, chatMessages.nextSibling);
        } else {
            chatContainer.appendChild(newContainer);
        }
        
        if (!toggleBtn) {
            const newBtn = document.createElement('button');
            newBtn.textContent = '▼ Hide Thought Process';
            newBtn.setAttribute('onclick', 'toggleThoughtProcess()');
            newBtn.style.cssText = 'margin: 5px 0; padding: 4px 12px; background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 4px; cursor: pointer; font-size: 12px;';
            newContainer.parentElement.insertBefore(newBtn, newContainer);
        }
        return;
    }
    
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        if (toggleBtn) toggleBtn.textContent = '▼ Hide Thought Process';
    } else {
        container.style.display = 'none';
        if (toggleBtn) toggleBtn.textContent = '▶ Show Thought Process';
    }
}

function startThoughtTimer() {
    thoughtStartTime = Date.now();
    if (thoughtTimer) clearInterval(thoughtTimer);
    thoughtTimer = setInterval(() => {
        const elapsed = Math.round((Date.now() - thoughtStartTime) / 1000);
        const statusEl = document.getElementById('thought-status');
        if (statusEl) {
            statusEl.textContent = `⏳ ${elapsed}s`;
        }
    }, 1000);
}

function stopThoughtTimer() {
    if (thoughtTimer) {
        clearInterval(thoughtTimer);
        thoughtTimer = null;
    }
    const statusEl = document.getElementById('thought-status');
    if (statusEl) {
        const elapsed = Math.round((Date.now() - thoughtStartTime) / 1000);
        statusEl.textContent = `✅ ${elapsed}s`;
    }
}

function addThoughtStep(step) {
    const container = document.getElementById('thought-process');
    if (!container) return;
    
    const stepEl = document.createElement('div');
    stepEl.className = 'thought-step';
    stepEl.dataset.step = step.step;
    stepEl.style.cssText = `
        padding: 4px 8px;
        margin-bottom: 3px;
        border-radius: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        background: ${step.status === 'active' ? '#1e293b' : '#0f172a'};
        border-left: 3px solid ${step.status === 'active' ? '#38bdf8' : '#334155'};
        opacity: ${step.status === 'active' ? 1 : 0.7};
    `;
    
    const icon = step.status === 'active' ? '⟳' : '✓';
    const iconColor = step.status === 'active' ? '#38bdf8' : '#22c55e';
    
    stepEl.innerHTML = `
        <span style="color: ${iconColor}; font-weight: bold;">${icon}</span>
        <span style="color: #f1f5f9; flex: 1;">${step.label}</span>
        <span style="color: #64748b; font-size: 10px;">${step.duration ? step.duration + 's' : ''}</span>
    `;
    
    container.appendChild(stepEl);
    container.scrollTop = container.scrollHeight;
}

function updateThoughtStep(stepNumber, status, data) {
    const container = document.getElementById('thought-process');
    if (!container) return;
    
    const steps = container.querySelectorAll('.thought-step');
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        if (step.dataset.step == stepNumber) {
            step.style.borderLeftColor = status === 'complete' ? '#22c55e' : '#38bdf8';
            step.style.opacity = status === 'complete' ? 0.7 : 1;
            const icon = step.querySelector('span:first-child');
            if (icon) {
                icon.textContent = status === 'complete' ? '✓' : '⟳';
                icon.style.color = status === 'complete' ? '#22c55e' : '#38bdf8';
            }
            break;
        }
    }
}

function completeAllThoughtSteps() {
    const container = document.getElementById('thought-process');
    if (!container) return;
    
    const steps = container.querySelectorAll('.thought-step');
    for (let i = 0; i < steps.length; i++) {
        const step = steps[i];
        step.style.borderLeftColor = '#22c55e';
        step.style.opacity = 0.7;
        const icon = step.querySelector('span:first-child');
        if (icon) {
            icon.textContent = '✓';
            icon.style.color = '#22c55e';
        }
    }
    stopThoughtTimer();
}

function clearThoughtProcess() {
    const container = document.getElementById('thought-process');
    if (container) {
        container.innerHTML = '';
    }
    stopThoughtTimer();
    const statusEl = document.getElementById('thought-status');
    if (statusEl) {
        statusEl.textContent = '';
    }
}

function updateThoughtProcessUI(thoughtSteps) {
    console.log("🧠 Updating thought process UI:", thoughtSteps);
    if (!thoughtSteps || !Array.isArray(thoughtSteps)) return;
    
    const container = document.getElementById('thought-steps-container');
    if (!container) {
        console.warn('Thought steps container not found');
        return;
    }
    
    // Clear existing content if this is a new set
    if (thoughtSteps.length > 0 && thoughtSteps[0].step === 1) {
        container.innerHTML = '';
    }
    
    thoughtSteps.forEach((step, index) => {
        const stepNum = step.step || step.step_number || index + 1;
        const label = step.label || step.description || 'Step';
        const desc = step.description || '';
        const status = step.status || 'complete';
        const statusColor = status === 'complete' ? '#34d399' : status === 'in-progress' ? '#fbbf24' : '#f87171';
        const statusIcon = status === 'complete' ? '✅' : status === 'in-progress' ? '⏳' : '❌';
        
        // Check if step already exists
        const existing = container.querySelector(`[data-step="${stepNum}"]`);
        if (existing) {
            // Update existing step
            const statusEl = existing.querySelector('.step-status');
            if (statusEl) {
                statusEl.textContent = status;
                statusEl.style.color = statusColor;
            }
            return;
        }
        
        const div = document.createElement('div');
        div.setAttribute('data-step', stepNum);
        div.style.cssText = 'padding: 8px 0; border-bottom: 1px solid #1e293b;';
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: #38bdf8;">
                    ${statusIcon} Step ${stepNum}: ${label}
                </span>
                <span class="step-status" style="font-size: 10px; color: ${statusColor};">${status}</span>
            </div>
            ${desc ? `<div style="color: #94a3b8; font-size: 11px; margin-left: 24px; margin-top: 2px;">${desc}</div>` : ''}
            ${step.data ? `<div style="color: #64748b; font-size: 10px; margin-left: 24px; margin-top: 2px;">${JSON.stringify(step.data)}</div>` : ''}
        `;
        container.appendChild(div);
    });
    
    // Auto-show thought process
    const stepsContainer = document.getElementById('thought-steps');
    if (stepsContainer && thoughtSteps.length > 0) {
        stepsContainer.style.display = 'block';
        const label = document.getElementById('thought-toggle-label');
        if (label) label.textContent = 'Hide';
    }
    
    // Store for later
    window._lastThoughtProcess = thoughtSteps;
}

// ============ SESSION FUNCTIONS ============
async function loadSessions() {
    const list = document.getElementById('session-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/v1/chat/sessions', getFetchOptions());
        if (!res.ok) throw new Error('Failed to load sessions');
        let sessions = await res.json();
        
        sessions.sort((a, b) => {
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            return new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at);
        });
        
        if (sessions.length === 0) {
            list.innerHTML = '<div class="metric-label" style="padding: 10px;">No saved chats. Start a new conversation!</div>';
            return;
        }
        
        let html = '';
        for (let i = 0; i < sessions.length; i++) {
            const s = sessions[i];
            const isActive = s.id === currentSessionId;
            const msgCount = s.message_count || 0;
            html += `
                <div class="session-item" onclick="loadSession(${s.id})" 
                     style="padding: 10px; margin-bottom: 6px; border-radius: 6px; cursor: pointer; 
                            background: ${isActive ? '#1e293b' : 'transparent'}; 
                            border: 1px solid ${isActive ? '#38bdf8' : 'transparent'};
                            ${s.pinned ? 'border-left: 3px solid #fbbf24;' : ''}
                            display: flex; flex-direction: column; gap: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="session-title" style="color: #f1f5f9; font-size: 13px; font-weight: ${isActive ? '600' : '400'};">
                            ${s.pinned ? '📌 ' : ''}${s.title || 'Untitled Chat'}
                        </span>
                        <span style="font-size: 10px; color: #64748b;">${new Date(s.updated_at || s.created_at).toLocaleDateString()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 10px; color: #64748b;">
                            💬 ${msgCount} message${msgCount !== 1 ? 's' : ''}
                        </span>
                        <div style="display: flex; gap: 6px;">
                            ${s.pinned ? 
                                `<button onclick="event.stopPropagation(); toggleUnpinSession(${s.id})" 
                                         style="background: none; border: none; color: #fbbf24; cursor: pointer; font-size: 10px;">
                                    📌 Unpin
                                </button>` :
                                `<button onclick="event.stopPropagation(); togglePinSession(${s.id})" 
                                         style="background: none; border: none; color: #64748b; cursor: pointer; font-size: 10px;">
                                    📌 Pin
                                </button>`
                            }
                        </div>
                    </div>
                </div>
            `;
        }
        list.innerHTML = html;
    } catch (e) {
        console.error('Error loading sessions:', e);
        list.innerHTML = '<div class="metric-label" style="color: #f87171;">Error loading sessions</div>';
    }
}

async function createNewSession() {
    try {
        const res = await fetch('/api/v1/chat/sessions', 
            getFetchOptions('POST', { title: 'New Chat' })
        );
        const data = await res.json();
        if (res.ok) {
            currentSessionId = data.id;
            const titleEl = document.getElementById('current-session-title');
            if (titleEl) titleEl.textContent = 'New Chat';
            const idEl = document.getElementById('session-id-display');
            if (idEl) idEl.textContent = '#' + data.id;
            const container = document.getElementById('chat-messages');
            if (container) {
                container.innerHTML = '<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">New chat session started. Ask me anything!</div>';
            }
            await loadSessions();
            clearThoughtProcess();
            return data.id;
        }
    } catch (e) {
        console.error('Error creating session:', e);
        showToast('Error creating session', 'error');
        return null;
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    try {
        const res = await fetch('/api/v1/chat/sessions/' + sessionId + '/messages', getFetchOptions());
        if (!res.ok) throw new Error('Failed to load messages');
        const data = await res.json();
        
        const titleEl = document.getElementById('current-session-title');
        if (titleEl) titleEl.textContent = data.title || 'Chat';
        const idEl = document.getElementById('session-id-display');
        if (idEl) idEl.textContent = '#' + sessionId;
        
        const container = document.getElementById('chat-messages');
        if (container) {
            if (data.messages && data.messages.length > 0) {
                let html = '';
                for (let i = 0; i < data.messages.length; i++) {
                    const m = data.messages[i];
                    const time = new Date(m.created_at || m.timestamp).toLocaleTimeString();
                    html += `
                        <div class="message ${m.role}" 
                             style="padding: 12px; background: ${m.role === 'user' ? '#1e293b' : '#0f172a'}; 
                                    border: 1px solid ${m.role === 'user' ? '#38bdf8' : '#334155'}; 
                                    border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                                    ${m.role === 'user' ? 'margin-left: auto;' : ''} 
                                    white-space: pre-wrap; word-wrap: break-word;">
                            ${m.content}
                            ${m.provider ? `<div style="font-size: 10px; color: #64748b; margin-top: 4px;">⚡ ${m.provider}</div>` : ''}
                            <div style="font-size: 10px; color: #64748b; margin-top: 4px;">${time}</div>
                        </div>
                    `;
                }
                container.innerHTML = html;
            } else {
                container.innerHTML = '<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">No messages yet. Start the conversation!</div>';
            }
            container.scrollTop = container.scrollHeight;
        }
        await loadSessions();
    } catch (e) {
        console.error('Error loading session:', e);
        showToast('Error loading session', 'error');
    }
}

// ============ SESSION PINNING ============
async function togglePinSession(sessionId) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}/pin`, 
            getFetchOptions('PATCH', { pinned: true })
        );
        if (res.ok) {
            await loadSessions();
            showToast('Session pinned! 📌', 'success');
        } else {
            showToast('Failed to pin session', 'error');
        }
    } catch (e) {
        console.error('Error pinning session:', e);
        showToast('Error pinning session', 'error');
    }
}

async function toggleUnpinSession(sessionId) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}/unpin`, 
            getFetchOptions('PATCH')
        );
        if (res.ok) {
            await loadSessions();
            showToast('Session unpinned', 'info');
        } else {
            showToast('Failed to unpin session', 'error');
        }
    } catch (e) {
        console.error('Error unpinning session:', e);
        showToast('Error unpinning session', 'error');
    }
}

// ============ SESSION SEARCH ============
function searchSessions(query) {
    const items = document.querySelectorAll('.session-item');
    query = query.toLowerCase().trim();
    let visibleCount = 0;
    
    items.forEach(item => {
        const title = item.querySelector('.session-title')?.textContent?.toLowerCase() || '';
        const matches = title.includes(query);
        item.style.display = matches ? 'flex' : 'none';
        if (matches) visibleCount++;
    });
    
    const list = document.getElementById('session-list');
    const noResults = document.getElementById('no-session-results');
    if (visibleCount === 0 && !noResults) {
        const msg = document.createElement('div');
        msg.id = 'no-session-results';
        msg.className = 'metric-label';
        msg.style.cssText = 'padding: 10px; color: #64748b; text-align: center;';
        msg.textContent = `No sessions found matching "${query}"`;
        if (list) list.appendChild(msg);
    } else if (noResults && visibleCount > 0) {
        noResults.remove();
    }
}

// ============ SESSION MANAGEMENT ============
function renameSession(newTitle) {
    if (!currentSessionId || !newTitle) {
        showToast('No session selected or title empty', 'error');
        return;
    }
    
    fetch('/api/v1/chat/sessions/' + currentSessionId, 
        getFetchOptions('PATCH', { title: newTitle })
    )
    .then(async (res) => {
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to rename session');
        }
        return res.json();
    })
    .then(() => {
        const titleEl = document.getElementById('current-session-title');
        if (titleEl) titleEl.textContent = newTitle;
        showToast('Session renamed successfully! ✏️', 'success');
        loadSessions();
    })
    .catch((err) => {
        console.error('Error renaming session:', err);
        showToast('Error renaming session: ' + err.message, 'error');
    });
}

function deleteCurrentSession() {
    if (!currentSessionId) {
        showToast('No session to delete', 'error');
        return;
    }
    
    if (!confirm('Delete this session and all its messages?')) return;
    
    fetch('/api/v1/chat/sessions/' + currentSessionId, 
        getFetchOptions('DELETE')
    )
    .then(async (res) => {
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to delete session');
        }
        return res.json();
    })
    .then(() => {
        currentSessionId = null;
        const titleEl = document.getElementById('current-session-title');
        if (titleEl) titleEl.textContent = 'New Chat';
        const idEl = document.getElementById('session-id-display');
        if (idEl) idEl.textContent = '';
        const container = document.getElementById('chat-messages');
        if (container) {
            container.innerHTML = '<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">👋 Session deleted. Create a new chat to get started.</div>';
        }
        loadSessions();
        showToast('Session deleted successfully 🗑️', 'info');
    })
    .catch((err) => {
        console.error('Error deleting session:', err);
        showToast('Error deleting session: ' + err.message, 'error');
    });
}

// ============ AUTO-SCROLL TOGGLE ============
function toggleAutoScroll() {
    autoScroll = !autoScroll;
    const btn = document.getElementById('auto-scroll-btn');
    if (btn) {
        btn.textContent = autoScroll ? '📌 Auto-scroll On' : '📌 Auto-scroll Off';
        btn.style.borderColor = autoScroll ? '#38bdf8' : '#334155';
        btn.style.color = autoScroll ? '#f1f5f9' : '#64748b';
    }
    showToast(autoScroll ? 'Auto-scroll enabled' : 'Auto-scroll disabled', 'info');
}

// ============ TYPING INDICATOR ============
function showTyping() {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    const typingEl = document.createElement('div');
    typingEl.id = 'typing-indicator';
    typingEl.className = 'message ai';
    typingEl.style.cssText = `
        padding: 12px;
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        margin-bottom: 10px;
        max-width: 85%;
        color: #94a3b8;
    `;
    typingEl.innerHTML = '⏳ Thinking...';
    container.appendChild(typingEl);
    if (autoScroll) container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const typingEl = document.getElementById('typing-indicator');
    if (typingEl) {
        typingEl.remove();
    }
}

// ============ RENDER STREAMING MARKDOWN ============
function renderStreamingMarkdown(element, content) {
    if (!element) return;
    
    try {
        if (!content || content.trim() === '') {
            element.innerHTML = '<span style="opacity: 0.5;">▍</span>';
            return;
        }
        
        if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
            let html = marked.parse(content, markdownConfig);
            html = html.replace(/<pre><code>/g, '<pre><code style="display: block; padding: 12px; overflow-x: auto;">');
            element.innerHTML = html;
        } else {
            element.innerHTML = content.replace(/\n/g, '<br>');
        }
        
        if (!content.endsWith(' ')) {
            element.innerHTML += '<span style="opacity: 0.3; animation: blink 1s infinite;">▍</span>';
        }
    } catch (e) {
        console.warn('Markdown parsing failed:', e);
        element.textContent = content || '';
    }
}

// ============ HIGHLIGHT CODE BLOCKS ============
function highlightCodeBlocks(container) {
    if (typeof hljs === 'undefined') return;
    
    container.querySelectorAll('pre code').forEach((block) => {
        try {
            hljs.highlightElement(block);
        } catch (e) {
            console.warn('Failed to highlight code block:', e);
        }
    });
    
    container.querySelectorAll('pre').forEach((pre) => {
        if (pre.querySelector('.code-copy-btn')) return;
        
        const code = pre.querySelector('code');
        if (code) {
            const copyBtn = document.createElement('button');
            copyBtn.className = 'code-copy-btn';
            copyBtn.style.cssText = `
                position: absolute;
                top: 8px;
                right: 8px;
                background: #1e293b;
                border: 1px solid #334155;
                color: #94a3b8;
                padding: 4px 10px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 10px;
                opacity: 0.7;
                transition: opacity 0.2s;
                z-index: 10;
            `;
            copyBtn.textContent = '📋 Copy';
            copyBtn.onclick = function(e) {
                e.stopPropagation();
                const codeText = code.textContent;
                navigator.clipboard.writeText(codeText).then(() => {
                    this.textContent = '✅ Copied!';
                    this.style.opacity = '1';
                    setTimeout(() => {
                        this.textContent = '📋 Copy';
                        this.style.opacity = '0.7';
                    }, 2000);
                });
            };
            pre.style.position = 'relative';
            pre.appendChild(copyBtn);
        }
    });
}

// ============ COPY, SHARE, EXPORT ============
function copyMessageContent(btn) {
    const messageDiv = btn.closest('.message.ai');
    const content = messageDiv?.querySelector('.markdown-body')?.textContent || '';
    navigator.clipboard.writeText(content).then(() => {
        btn.textContent = '✅ Copied!';
        setTimeout(() => btn.textContent = '📋 Copy', 2000);
    });
}

function shareMessage(btn) {
    const messageDiv = btn.closest('.message.ai');
    const content = messageDiv?.querySelector('.markdown-body')?.textContent || '';
    if (navigator.share) {
        navigator.share({ title: 'PersonaVault Chat', text: content }).catch(() => {});
    } else {
        navigator.clipboard.writeText(content).then(() => {
            showToast('Message copied to clipboard! 📋', 'success');
        });
    }
}

function exportMessage(btn) {
    const messageDiv = btn.closest('.message.ai');
    const content = messageDiv?.querySelector('.markdown-body')?.textContent || '';
    if (!content) {
        showToast('No content to export', 'error');
        return;
    }
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `personavault-export-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Message exported! 📥', 'success');
}

// ============ SEND MESSAGE ============
async function sendMessage() {
    const input = document.getElementById('chat-input');
    if (!input) {
        console.error('Chat input not found');
        return;
    }
    
    const query = input.value.trim();
    if (!query) {
        showToast('Please enter a message', 'info');
        return;
    }
    
    if (query.length > MAX_MESSAGE_LENGTH) {
        showToast(`Message exceeds ${MAX_MESSAGE_LENGTH} characters`, 'error');
        return;
    }
    
    input.value = '';
    await sendChatMessage(query);
}

// Wrapper to match frontend call
async function sendChatMessageStream() {
    await sendMessage();
}

// ============ QUICK PROMPTS ============
function sendQuickPrompt(prompt) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = prompt;
        sendMessage();
    }
}

// ============ MAIN CHAT FUNCTION ============
async function sendChatMessage(query) {
    // Get provider from UI dropdown or backend default
    const providerSelect = document.getElementById("chat-provider");
    const provider = providerSelect ? providerSelect.value : await getPrimaryProvider();
    
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    // Add user message
    container.innerHTML += `
        <div class="message user" 
             style="padding: 12px; background: #1e293b; border: 1px solid #38bdf8; 
                    border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                    margin-left: auto; white-space: pre-wrap; word-wrap: break-word;">
            ${query}
            <div style="font-size: 10px; color: #64748b; margin-top: 4px;">${new Date().toLocaleTimeString()}</div>
        </div>
    `;
    
    if (autoScroll) container.scrollTop = container.scrollHeight;
    
    showTyping();
    startThoughtTimer();
    addThoughtStep({ step: 1, label: 'Initializing', description: 'Processing your request...', status: 'active' });
    
    try {
                if (!query) {
            console.error("DEBUG: Query is empty!");
            showToast("Query is empty!", "error");
            hideTyping();
            stopThoughtTimer();
            return;
        }
        const requestBody = {
            query: query,
            provider: provider,
            track_thoughts: true
        };
        
        if (currentSessionId && typeof currentSessionId === 'number') {
            requestBody.session_id = currentSessionId;
        }
        
        console.log("DEBUG: requestBody:", JSON.stringify(requestBody));
        console.log('📤 Sending request with provider:', provider);
        
        const response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        
        if (response.status === 401) {
            hideTyping();
            stopThoughtTimer();
            showToast('Session expired. Please refresh.', 'error');
            return;
        }
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error:', response.status, errorText);
            throw new Error(`Server error: ${response.status}`);
        }
        
        // Create AI message container
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message ai';
        messageDiv.style.cssText = `
            padding: 16px;
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            margin-bottom: 10px;
            max-width: 85%;
            overflow: hidden;
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'markdown-body';
        contentDiv.style.cssText = 'color: #e2e8f0; font-size: 14px; line-height: 1.6; min-height: 20px; white-space: pre-wrap; word-wrap: break-word;';
        contentDiv.textContent = '▍';
        messageDiv.appendChild(contentDiv);
        
        const providerDiv = document.createElement('div');
        providerDiv.style.cssText = 'font-size: 10px; color: #64748b; margin-top: 8px;';
        providerDiv.textContent = `⚡ ${provider}`;
        messageDiv.appendChild(providerDiv);
        
        const timestampDiv = document.createElement('div');
        timestampDiv.style.cssText = 'font-size: 10px; color: #64748b; margin-top: 4px;';
        timestampDiv.textContent = new Date().toLocaleTimeString();
        messageDiv.appendChild(timestampDiv);
        
        const actionsDiv = document.createElement('div');
        actionsDiv.style.cssText = 'margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap; border-top: 1px solid #1e293b; padding-top: 8px;';
        actionsDiv.innerHTML = `
            <button onclick="copyMessageContent(this)" style="background: #1e293b; border: none; color: #94a3b8; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px;">📋 Copy</button>
            <button onclick="shareMessage(this)" style="background: #1e293b; border: none; color: #94a3b8; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px;">🔗 Share</button>
            <button onclick="exportMessage(this)" style="background: #1e293b; border: none; color: #94a3b8; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-size: 11px;">📥 Export</button>
        `;
        messageDiv.appendChild(actionsDiv);
        
        container.appendChild(messageDiv);
        if (autoScroll) container.scrollTop = container.scrollHeight;
        
        // ============================================================
        // PROCESS STREAM
        // ============================================================
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullContent = '';
        let buffer = '';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                console.log('📡 Stream complete');
                break;
            }
        
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
        
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine || trimmedLine.startsWith(':')) continue;
        
                if (trimmedLine.startsWith('data: ')) {
                    const dataStr = trimmedLine.slice(6).trim();
                    if (dataStr === '[DONE]') continue;
        
                    try {
                        const data = JSON.parse(dataStr);
        
                        if (data.content !== undefined && data.content !== null && data.content !== 'undefined') {
                            fullContent += data.content;
                            contentDiv.textContent = fullContent + '▍';
                            if (autoScroll) container.scrollTop = container.scrollHeight;
                        }
        
                        if (data.thought) {
                            updateThoughtProcessUI([data.thought]);
                            // Store for later display
                            if (!window._lastThoughtProcess) window._lastThoughtProcess = [];
                            window._lastThoughtProcess.push(data.thought);
                        }
                        if (data.thought_process) {
                            updateThoughtProcessUI(data.thought_process);
                            // Store for later display
                            window._lastThoughtProcess = data.thought_process;
                            // Auto-show thought process if available
                            const stepsContainer = document.getElementById('thought-steps');
                            if (stepsContainer) {
                                stepsContainer.style.display = 'block';
                                const label = document.getElementById('thought-toggle-label');
                                if (label) label.textContent = 'Hide';
                            }
                        }
        
                        if (data.session_id) {
                            currentSessionId = data.session_id;
                            const idEl = document.getElementById('session-id-display');
                            if (idEl) idEl.textContent = '#' + data.session_id;
                        }
        
                        if (data.error) {
                            console.error('Stream error:', data.error);
                        }
                    } catch (e) {
                        if (dataStr && !dataStr.startsWith('{')) {
                            fullContent += dataStr;
                            contentDiv.textContent = fullContent + '▍';
                            if (autoScroll) container.scrollTop = container.scrollHeight;
                        }
                    }
                }
            }
        }
        
        // --- FINAL RENDER ---
        if (contentDiv) {
            const cursor = contentDiv.querySelector('span[style*="blink"]');
            if (cursor) cursor.remove();
        
            if (fullContent) {
        console.log("DEBUG: fullContent is:", fullContent);
                if (typeof marked !== 'undefined' && typeof marked.parse === 'function') {
                    try {
                        let html = marked.parse(fullContent, markdownConfig);
                        html = html.replace(/<pre><code>/g, '<pre><code style="display: block; padding: 12px; overflow-x: auto;">');
                        contentDiv.innerHTML = html;
                    } catch (e) {
                        contentDiv.textContent = fullContent;
                    }
                } else {
                    contentDiv.textContent = fullContent;
                }
            }
        }
        
        highlightCodeBlocks(messageDiv);
        completeAllThoughtSteps();
        hideTyping();
        stopThoughtTimer();
        await loadSessions();
        
    } catch (e) {
        console.error('Chat error:', e);
        hideTyping();
        stopThoughtTimer();
        showToast('Error: ' + (e.message || 'Failed to send message'), 'error');
    }
}

// ============ BLINKING CURSOR CSS ============
const style = document.createElement('style');
style.textContent = `
    @keyframes blink {
        0%, 50% { opacity: 0.3; }
        51%, 100% { opacity: 1; }
    }
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (typeof sendMessage === 'function') {
                    sendMessage();
                }
            }
            if (e.key === 'Escape') {
                this.value = '';
            }
        });
        
        const counter = document.createElement('div');
        counter.style.cssText = 'text-align: right; font-size: 11px; color: #64748b; margin-top: 4px;';
        counter.textContent = '0 / 2000';
        input.parentNode.appendChild(counter);
        
        input.addEventListener('input', function() {
            const count = this.value.length;
            counter.textContent = `${count} / ${MAX_MESSAGE_LENGTH}`;
            counter.style.color = count > MAX_MESSAGE_LENGTH - 100 ? '#f87171' : '#64748b';
        });
    }
    
    document.addEventListener('keydown', function(e) {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            if (typeof sendMessage === 'function') {
                sendMessage();
            }
        }
    });
    
    // Load provider and sessions
    loadProviderIntoUI();
    loadSessions();
    
    if (!currentSessionId) {
        setTimeout(() => {
            createNewSession();
        }, 500);
    }
});

// ============ EXPOSE GLOBALLY ============
window.sendChatMessageStream = sendChatMessageStream;
window.sendMessage = sendMessage;
window.loadSessions = loadSessions;
window.loadSession = loadSession;
window.createNewSession = createNewSession;
window.renameSession = renameSession;
window.deleteCurrentSession = deleteCurrentSession;
window.showToast = showToast;
window.toggleThoughtProcess = toggleThoughtProcess;
window.clearThoughtProcess = clearThoughtProcess;
window.searchSessions = searchSessions;
window.togglePinSession = togglePinSession;
window.toggleUnpinSession = toggleUnpinSession;
window.sendQuickPrompt = sendQuickPrompt;
window.copyMessageContent = copyMessageContent;
window.shareMessage = shareMessage;
window.exportMessage = exportMessage;
window.toggleAutoScroll = toggleAutoScroll;
window.renderStreamingMarkdown = renderStreamingMarkdown;
window.highlightCodeBlocks = highlightCodeBlocks;
window.updateThoughtProcessUI = updateThoughtProcessUI;
window.addThoughtStep = addThoughtStep;
window.updateThoughtStep = updateThoughtStep;
window.completeAllThoughtSteps = completeAllThoughtSteps;
window.startThoughtTimer = startThoughtTimer;
window.stopThoughtTimer = stopThoughtTimer;
window.showTyping = showTyping;
window.hideTyping = hideTyping;
window.getFetchOptions = getFetchOptions;
window.loadProviderIntoUI = loadProviderIntoUI;
window.getPrimaryProvider = getPrimaryProvider;

console.log('✅ chat.js loaded - All chat functions available');

// Direct handler for the send button that works with dynamic content
function setupChatHandlers() {
    const sendBtn = document.getElementById('send-chat-btn');
    if (sendBtn) {
        // Remove any existing listeners
        const newBtn = sendBtn.cloneNode(true);
        sendBtn.parentNode.replaceChild(newBtn, sendBtn);
        
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔵 Send button clicked');
            if (typeof sendChatMessageStream === 'function') {
                sendChatMessageStream();
            } else {
                console.error('sendChatMessageStream not available');
                // Try to load it
                const script = document.createElement('script');
                script.src = '/static/js/chat.js';
                document.head.appendChild(script);
                setTimeout(() => {
                    if (typeof sendChatMessageStream === 'function') {
                        sendChatMessageStream();
                    }
                }, 500);
            }
        });
        console.log('✅ Send button handler attached');
    }
}

// Run setup when DOM is ready and when chat tab loads
document.addEventListener('DOMContentLoaded', setupChatHandlers);

// Also expose it to be called from tab load
window.setupChatHandlers = setupChatHandlers;
console.log('✅ Chat handlers ready');

// Sync chat provider with dashboard provider
async function syncChatProviderWithDashboard() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error('Failed to fetch provider');
        const data = await res.json();
        const provider = data.primary_provider || 'ollama';
        
        // Update the chat dropdown
        const chatSelect = document.getElementById('chat-provider-select');
        if (chatSelect) {
            // Find and select the provider
            let found = false;
            for (let option of chatSelect.options) {
                if (option.value.toLowerCase() === provider.toLowerCase()) {
                    chatSelect.value = option.value;
                    found = true;
                    break;
                }
            }
            // If not found, add it
            if (!found && provider !== 'ollama') {
                const option = document.createElement('option');
                option.value = provider.toLowerCase();
                option.textContent = `☁️ ${provider} (Cloud)`;
                chatSelect.appendChild(option);
                chatSelect.value = provider.toLowerCase();
            }
            console.log(`✅ Chat provider synced to: ${provider}`);
        }
        
        // Update the status display
        const statusEl = document.getElementById('primary-ai-provider-status-chat');
        if (statusEl) {
            statusEl.textContent = provider;
            statusEl.className = 'tag tag-info';
        }
        
        return provider;
    } catch (e) {
        console.error('Error syncing chat provider:', e);
        return 'ollama';
    }
}

// Expose the function globally
window.syncChatProviderWithDashboard = syncChatProviderWithDashboard;

// When chat provider changes, update the global provider
document.addEventListener('change', function(e) {
    if (e.target.id === 'chat-provider-select') {
        const provider = e.target.value;
        if (provider && typeof updatePrimaryAIProvider === 'function') {
            updatePrimaryAIProvider(provider);
            console.log(`🔄 Chat provider changed to: ${provider}, updating global...`);
        } else if (provider) {
            // Fallback: direct API call
            fetch('/api/v1/admin/dashboard/config/primary-ai-provider', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: provider })
            }).then(() => {
                console.log(`✅ Provider updated to: ${provider}`);
                // Update all status displays
                document.querySelectorAll('.provider-status').forEach(el => {
                    el.textContent = provider;
                });
            });
        }
    }
});
console.log('✅ Provider sync function added');

// ============ SESSION MANAGEMENT FUNCTIONS ============
// These are added to chat.js for global access

let currentSessionId = null;
let currentSessionTitle = '';

async function loadSessions() {
    const container = document.getElementById('session-list');
    if (!container) return;
    
    try {
        const res = await fetch('/api/v1/chat/sessions');
        if (!res.ok) throw new Error('Failed to load sessions');
        const sessions = await res.json();
        console.log('📋 Sessions loaded:', sessions);
        
        if (sessions.length === 0) {
            container.innerHTML = `<div class="metric-label" style="padding: 20px; text-align: center; color: #64748b;">No sessions yet.<br>Click "New" to start chatting!</div>`;
            return;
        }
        
        container.innerHTML = sessions.map(s => {
            const isActive = s.id === currentSessionId;
            const msgCount = s.message_count || 0;
            const title = s.title || 'Untitled Chat';
            const date = new Date(s.updated_at || s.created_at).toLocaleDateString();
            
            return `
                <div class="session-item" 
                     data-id="${s.id}" 
                     onclick="loadSession(${s.id})"
                     style="padding: 10px; margin-bottom: 6px; border-radius: 6px; cursor: pointer; 
                            background: ${isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent'}; 
                            border: 1px solid ${isActive ? '#38bdf8' : 'transparent'};
                            transition: all 0.2s;
                            ${isActive ? 'box-shadow: 0 0 20px rgba(56, 189, 248, 0.05);' : ''}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: ${isActive ? '#38bdf8' : '#f1f5f9'}; font-size: 13px; font-weight: ${isActive ? '600' : '400'};">
                            ${title}
                        </span>
                        <span style="font-size: 10px; color: #64748b;">${date}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                        <span style="font-size: 10px; color: #64748b;">
                            💬 ${msgCount} message${msgCount !== 1 ? 's' : ''}
                        </span>
                        <div style="display: flex; gap: 6px;">
                            <button onclick="event.stopPropagation(); renameSessionDirect(${s.id})" 
                                    style="background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 10px;">
                                ✏️
                            </button>
                            <button onclick="event.stopPropagation(); deleteSession(${s.id})" 
                                    style="background: none; border: none; color: #f87171; cursor: pointer; font-size: 10px;">
                                🗑️
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Error loading sessions:', e);
        container.innerHTML = '<div style="color: #f87171; padding: 20px; text-align: center;">Error loading sessions</div>';
    }
}

async function createNewSession() {
    try {
        const res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
        if (!res.ok) throw new Error('Failed to create session');
        const data = await res.json();
        currentSessionId = data.id;
        currentSessionTitle = data.title || 'New Chat';
        updateSessionUI(data.id, currentSessionTitle);
        clearChatMessages();
        await loadSessions();
        showToast('✅ New chat session created!', 'success');
        return data.id;
    } catch (e) {
        console.error('Error creating session:', e);
        showToast('Error creating session: ' + e.message, 'error');
        return null;
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}/messages`);
        if (!res.ok) throw new Error('Failed to load messages');
        const data = await res.json();
        currentSessionTitle = data.title || 'Chat';
        updateSessionUI(sessionId, currentSessionTitle);
        
        const container = document.getElementById('chat-messages');
        if (container) {
            if (data.messages && data.messages.length > 0) {
                container.innerHTML = data.messages.map(m => {
                    const time = new Date(m.created_at || m.timestamp).toLocaleTimeString();
                    return `
                        <div class="message ${m.role}" 
                             style="padding: 12px; background: ${m.role === 'user' ? '#1e293b' : '#0f172a'}; 
                                    border: 1px solid ${m.role === 'user' ? '#38bdf8' : '#334155'}; 
                                    border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                                    ${m.role === 'user' ? 'margin-left: auto;' : ''} 
                                    white-space: pre-wrap; word-wrap: break-word;">
                            ${m.content}
                            ${m.provider ? `<div style="font-size: 10px; color: #64748b; margin-top: 4px;">⚡ ${m.provider}</div>` : ''}
                            <div style="font-size: 10px; color: #64748b; margin-top: 4px;">${time}</div>
                        </div>
                    `;
                }).join('');
                container.scrollTop = container.scrollHeight;
            } else {
                container.innerHTML = `<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">
                    👋 Continue your conversation here.
                </div>`;
            }
        }
        await loadSessions();
        clearThoughtProcess();
    } catch (e) {
        console.error('Error loading session:', e);
        showToast('Error loading session: ' + e.message, 'error');
    }
}

function updateSessionUI(sessionId, title) {
    const titleEl = document.getElementById('current-session-title');
    if (titleEl) titleEl.textContent = title;
    const idEl = document.getElementById('session-id-display');
    if (idEl) idEl.textContent = `#${sessionId}`;
}

async function renameSession() {
    if (!currentSessionId) {
        showToast('No session selected', 'error');
        return;
    }
    const newTitle = prompt('Enter new session name:', currentSessionTitle || 'Untitled Chat');
    if (newTitle && newTitle.trim()) {
        await renameSessionDirect(currentSessionId, newTitle.trim());
    }
}

async function renameSessionDirect(sessionId, newTitle) {
    if (!newTitle) {
        const promptTitle = prompt('Enter new session name:', '');
        if (!promptTitle) return;
        newTitle = promptTitle;
    }
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (!res.ok) throw new Error('Failed to rename session');
        if (sessionId === currentSessionId) {
            currentSessionTitle = newTitle;
            const titleEl = document.getElementById('current-session-title');
            if (titleEl) titleEl.textContent = newTitle;
        }
        await loadSessions();
        showToast('✅ Session renamed!', 'success');
    } catch (e) {
        console.error('Error renaming session:', e);
        showToast('Error renaming session: ' + e.message, 'error');
    }
}

async function deleteCurrentSession() {
    if (!currentSessionId) {
        showToast('No session to delete', 'error');
        return;
    }
    if (!confirm(`Delete "${currentSessionTitle}" and all its messages?`)) return;
    await deleteSession(currentSessionId);
}

async function deleteSession(sessionId) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}`, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete session');
        if (sessionId === currentSessionId) {
            currentSessionId = null;
            currentSessionTitle = '';
            const titleEl = document.getElementById('current-session-title');
            if (titleEl) titleEl.textContent = 'New Chat';
            const idEl = document.getElementById('session-id-display');
            if (idEl) idEl.textContent = '';
            clearChatMessages();
        }
        await loadSessions();
        showToast('🗑️ Session deleted', 'info');
    } catch (e) {
        console.error('Error deleting session:', e);
        showToast('Error deleting session: ' + e.message, 'error');
    }
}

function refreshSessions() {
    loadSessions();
}

function searchSessions(query) {
    const items = document.querySelectorAll('.session-item');
    const searchTerm = query.toLowerCase().trim();
    items.forEach(item => {
        const title = item.querySelector('span:first-child')?.textContent?.toLowerCase() || '';
        item.style.display = title.includes(searchTerm) ? 'flex' : 'none';
    });
}

async function exportCurrentSession() {
    if (!currentSessionId) {
        showToast('No session selected', 'error');
        return;
    }
    try {
        const res = await fetch(`/api/v1/chat/sessions/${currentSessionId}/messages`);
        const data = await res.json();
        let content = `# Chat Export\n`;
        content += `Session: ${data.title || 'Untitled'}\n`;
        content += `Date: ${new Date().toISOString()}\n\n`;
        data.messages?.forEach(m => {
            content += `## ${m.role.toUpperCase()}\n${m.content}\n\n`;
        });
        const blob = new Blob([content], {type: 'text/markdown'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat_${currentSessionId}_${new Date().toISOString().slice(0,10)}.md`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('📥 Chat exported!', 'success');
    } catch (e) {
        showToast('Error exporting chat: ' + e.message, 'error');
    }
}

function clearChatMessages() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = `<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">
            👋 Start a new conversation or select a session.
        </div>`;
    }
}

// Expose session functions globally
window.loadSessions = loadSessions;
window.createNewSession = createNewSession;
window.loadSession = loadSession;
window.renameSession = renameSession;
window.deleteCurrentSession = deleteCurrentSession;
window.deleteSession = deleteSession;
window.refreshSessions = refreshSessions;
window.searchSessions = searchSessions;
window.exportCurrentSession = exportCurrentSession;
window.renameSessionDirect = renameSessionDirect;

console.log('✅ Chat session management functions loaded globally');

// ============ THOUGHT PROCESS DISPLAY ============
// Enhanced thought process functions for better UI

// Main function to toggle thought process visibility
window.toggleThoughtProcess = function() {
    const container = document.getElementById('thought-steps');
    const label = document.getElementById('thought-toggle-label');
    if (!container) {
        console.warn('Thought steps container not found');
        return;
    }
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        if (label) label.textContent = 'Hide';
        // Load thought process if not already loaded
        const stepsContainer = document.getElementById('thought-steps-container');
        if (stepsContainer && stepsContainer.children.length <= 1) {
            // Try to get thought process from last response
            const lastResponse = window._lastThoughtProcess;
            if (lastResponse && lastResponse.length > 0) {
                window.renderThoughtSteps(lastResponse);
            }
        }
    } else {
        container.style.display = 'none';
        if (label) label.textContent = 'Show';
    }
};

// Render thought steps from API response
window.renderThoughtSteps = function(thoughtProcess) {
    const container = document.getElementById('thought-steps-container');
    if (!container) return;
    
    if (!thoughtProcess || thoughtProcess.length === 0) {
        container.innerHTML = '<div style="color: #64748b; font-style: italic;">No thought steps available for this response.</div>';
        return;
    }
    
    container.innerHTML = '';
    thoughtProcess.forEach((step, index) => {
        const div = document.createElement('div');
        div.className = 'thought-step';
        div.style.cssText = 'padding: 8px 0; border-bottom: 1px solid #1e293b;';
        
        const stepNum = step.step || step.step_number || index + 1;
        const label = step.label || step.description || 'Step';
        const desc = step.description || '';
        const status = step.status || 'complete';
        const statusColor = status === 'complete' ? '#34d399' : status === 'in-progress' ? '#fbbf24' : '#f87171';
        const statusIcon = status === 'complete' ? '✅' : status === 'in-progress' ? '⏳' : '❌';
        
        div.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; color: #38bdf8;">
                    ${statusIcon} Step ${stepNum}: ${label}
                </span>
                <span style="font-size: 10px; color: ${statusColor};">${status}</span>
            </div>
            ${desc ? `<div style="color: #94a3b8; font-size: 11px; margin-left: 24px; margin-top: 2px;">${desc}</div>` : ''}
            ${step.data ? `<div style="color: #64748b; font-size: 10px; margin-left: 24px; margin-top: 2px;">${JSON.stringify(step.data)}</div>` : ''}
        `;
        container.appendChild(div);
    });
    
    // Show the thought process container
    const stepsContainer = document.getElementById('thought-steps');
    if (stepsContainer) {
        stepsContainer.style.display = 'block';
        const label = document.getElementById('thought-toggle-label');
        if (label) label.textContent = 'Hide';
    }
};

// Override the message handler to capture thought process
const originalSendMessage = window.sendChatMessageStream;
if (originalSendMessage) {
    window.sendChatMessageStream = async function() {
        const result = await originalSendMessage.apply(this, arguments);
        // Check if thought process exists in the response
        const thoughtProcess = window._lastThoughtProcess;
        if (thoughtProcess && thoughtProcess.length > 0) {
            console.log('🧠 Thought process captured:', thoughtProcess);
        }
        return result;
    };
}

console.log('✅ Thought process display functions loaded');
