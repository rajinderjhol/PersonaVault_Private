// ============================================================
// CHAT FUNCTIONS - Complete chat UI
// ============================================================

let currentSessionId = null;
let thoughtSteps = [];
let thoughtTimer = null;
let thoughtStartTime = null;

// ============ SESSIONS ============
async function loadSessions() {
    const list = document.getElementById('session-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/v1/chat/sessions');
        if (!res.ok) throw new Error('Failed to load sessions');
        const sessions = await res.json();
        
        if (sessions.length === 0) {
            list.innerHTML = '<div class="metric-label" style="padding: 10px;">No saved chats. Start a new conversation!</div>';
            return;
        }
        
        let html = '';
        for (let i = 0; i < sessions.length; i++) {
            const s = sessions[i];
            const isActive = s.id === currentSessionId;
            html += `
                <div class="session-item" onclick="loadSession(${s.id})" 
                     style="padding: 10px; margin-bottom: 6px; border-radius: 6px; cursor: pointer; 
                            background: ${isActive ? '#1e293b' : 'transparent'}; 
                            border: 1px solid ${isActive ? '#38bdf8' : 'transparent'};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: #f1f5f9; font-size: 13px; font-weight: ${isActive ? '600' : '400'};">
                            ${s.title || 'Untitled Chat'}
                        </span>
                        <span style="font-size: 10px; color: #64748b;">${new Date(s.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div style="font-size: 10px; color: #64748b; margin-top: 2px;">${s.message_count || 0} messages</div>
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
        const res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
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
        const res = await fetch('/api/v1/chat/sessions/' + sessionId + '/messages');
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
                    html += `
                        <div class="message ${m.role}" 
                             style="padding: 12px; background: ${m.role === 'user' ? '#1e293b' : '#0f172a'}; 
                                    border: 1px solid ${m.role === 'user' ? '#38bdf8' : '#334155'}; 
                                    border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                                    ${m.role === 'user' ? 'margin-left: auto;' : ''} 
                                    white-space: pre-wrap; word-wrap: break-word;">
                            ${m.content}
                            ${m.provider ? `<div style="font-size: 10px; color: #64748b; margin-top: 4px;">⚡ ${m.provider}</div>` : ''}
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
        clearThoughtProcess();
    } catch (e) {
        console.error('Error loading session:', e);
        showToast('Error loading messages', 'error');
    }
}

function refreshSessions() { loadSessions(); }

// ============ THOUGHT PROCESS ============
function toggleThoughtProcess() {
    const container = document.getElementById('thought-steps');
    const label = document.getElementById('thought-toggle-label');
    if (!container) return;
    
    if (container.style.display === 'none') {
        container.style.display = 'block';
        if (label) label.textContent = 'Hide';
    } else {
        container.style.display = 'none';
        if (label) label.textContent = 'Show';
    }
}

function addThoughtStep(step) {
    const container = document.getElementById('thought-steps-container');
    if (!container) return;
    
    // Remove placeholder if present
    if (container.children.length === 1 && container.children[0].textContent.includes('No thought steps')) {
        container.innerHTML = '';
    }
    
    // Show the thought process container
    const processContainer = document.getElementById('thought-process-container');
    if (processContainer) processContainer.style.display = 'block';
    
    const stepsContainer = document.getElementById('thought-steps');
    if (stepsContainer) stepsContainer.style.display = 'block';
    
    const label = document.getElementById('thought-toggle-label');
    if (label) label.textContent = 'Hide';
    
    const div = document.createElement('div');
    div.className = `thought-step ${step.status || 'pending'}`;
    div.id = `thought-step-${step.step}`;
    
    const statusIcons = {
        'in-progress': '⏳',
        'complete': '✅',
        'failed': '❌',
        'pending': '⏸️'
    };
    
    div.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1e293b;">
            <div>
                <span style="font-weight: 600; color: #38bdf8;">
                    ${statusIcons[step.status] || '⏳'} Step ${step.step}: ${step.label}
                </span>
                <span style="color: #64748b; font-size: 11px; margin-left: 8px;">
                    ${step.duration ? step.duration.toFixed(2) + 's' : ''}
                </span>
            </div>
            <span style="font-size: 10px; color: ${step.status === 'in-progress' ? '#fbbf24' : step.status === 'complete' ? '#34d399' : '#f87171'};">
                ${step.status || 'pending'}
            </span>
        </div>
        <div style="color: #94a3b8; font-size: 12px; padding-left: 20px; padding-bottom: 4px;">
            ${step.description || ''}
        </div>
        ${step.data ? `<div style="color: #64748b; font-size: 10px; padding-left: 20px;">📊 ${JSON.stringify(step.data)}</div>` : ''}
        ${step.error ? `<div style="color: #f87171; font-size: 11px; padding-left: 20px;">❌ ${step.error}</div>` : ''}
    `;
    
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function updateThoughtStep(stepIndex, status, data) {
    const el = document.getElementById(`thought-step-${stepIndex}`);
    if (!el) return;
    
    el.className = `thought-step ${status}`;
    const statusEl = el.querySelector('span:last-child');
    if (statusEl) {
        statusEl.textContent = status;
        statusEl.style.color = status === 'in-progress' ? '#fbbf24' : status === 'complete' ? '#34d399' : '#f87171';
    }
}

function startThoughtTimer() {
    const timerEl = document.getElementById('thought-timer');
    if (!timerEl) return;
    thoughtStartTime = Date.now();
    if (thoughtTimer) clearInterval(thoughtTimer);
    thoughtTimer = setInterval(() => {
        const elapsed = (Date.now() - thoughtStartTime) / 1000;
        timerEl.textContent = `⏱️ ${elapsed.toFixed(1)}s`;
    }, 100);
}

function stopThoughtTimer() {
    if (thoughtTimer) {
        clearInterval(thoughtTimer);
        thoughtTimer = null;
    }
}

function clearThoughtProcess() {
    const container = document.getElementById('thought-steps-container');
    if (container) {
        container.innerHTML = '<div style="color: #64748b; font-style: italic; padding: 10px;">No thought steps yet. Send a message to see the AI\'s reasoning.</div>';
    }
    stopThoughtTimer();
    const timerEl = document.getElementById('thought-timer');
    if (timerEl) timerEl.textContent = '';
    
    // Hide the thought process container
    const processContainer = document.getElementById('thought-process-container');
    if (processContainer) processContainer.style.display = 'none';
}

// ============ PROVIDER SYNC ============
async function syncChatProviderWithDashboard() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error('Failed to fetch provider');
        const data = await res.json();
        const provider = data.primary_provider || 'ollama';
        
        const chatSelect = document.getElementById('chat-provider-select');
        if (chatSelect) {
            let found = false;
            for (let option of chatSelect.options) {
                if (option.value.toLowerCase() === provider.toLowerCase()) {
                    chatSelect.value = option.value;
                    found = true;
                    break;
                }
            }
            if (!found && provider !== 'ollama') {
                const newOption = document.createElement('option');
                newOption.value = provider.toLowerCase();
                newOption.textContent = `☁️ ${provider} (Cloud)`;
                chatSelect.appendChild(newOption);
                chatSelect.value = provider.toLowerCase();
            }
            const statusEl = document.getElementById('primary-ai-provider-status-chat');
            if (statusEl) {
                statusEl.textContent = provider;
                statusEl.className = 'tag tag-info';
            }
        }
        return provider;
    } catch (e) {
        console.error('Error syncing provider:', e);
        const chatSelect = document.getElementById('chat-provider-select');
        if (chatSelect) chatSelect.value = 'ollama';
        return 'ollama';
    }
}

// ============ SEND CHAT MESSAGE ============
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const query = input.value.trim();
    if (!query) return;
    
    console.log('📤 Sending chat message:', query);
    
    // Clear previous thought process
    clearThoughtProcess();
    
    // Create session if none exists
    if (!currentSessionId) {
        const newId = await createNewSession();
        if (!newId) {
            showToast('Please wait for session to create', 'error');
            return;
        }
    }
    
    const providerSelect = document.getElementById('chat-provider-select');
    const provider = providerSelect ? providerSelect.value : 'ollama';
    
    // Add user message
    addMessage('user', query);
    input.value = '';
    
    // Show thought process
    startThoughtTimer();
    
    // Add initial thought step
    addThoughtStep({
        step: 1,
        label: 'Understanding',
        description: `Processing query: "${query}"`,
        status: 'in-progress',
        duration: 0
    });
    
    // Show typing indicator
    showTyping();
    
    try {
        const res = await fetch('/api/v1/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: query,
                provider: provider,
                session_id: currentSessionId,
                track_thoughts: true
            })
        });
        
        const data = await res.json();
        hideTyping();
        stopThoughtTimer();
        
        // Display thought process from response
        if (data.thought_process && data.thought_process.length > 0) {
            // Update the first step
            const firstStep = data.thought_process[0];
            if (firstStep) {
                updateThoughtStep(1, firstStep.status || 'complete', firstStep.data);
            }
            // Add remaining steps
            for (let i = 1; i < data.thought_process.length; i++) {
                const step = data.thought_process[i];
                addThoughtStep({
                    step: step.step || i + 1,
                    label: step.label || 'Step',
                    description: step.description || '',
                    status: step.status || 'complete',
                    duration: step.duration || 0,
                    data: step.data
                });
            }
        } else {
            updateThoughtStep(1, 'complete', {});
        }
        
        if (res.ok && !data.error) {
            // Show swarm agents
            if (data.agent_status) {
                showSwarmActivity(data.agent_status);
            }
            let response = data.response || 'No response';
            if (data.confidence) {
                response += `\n\n📊 Confidence: ${Math.round(data.confidence * 100)}%`;
            }
            if (data.provider) {
                response += `\n⚡ Provider: ${data.provider}`;
            }
            addMessage('ai', response);
            
            const statusEl = document.getElementById('primary-ai-provider-status-chat');
            if (statusEl) {
                statusEl.textContent = data.provider || provider;
                statusEl.className = 'tag tag-success';
            }
            
            loadSessions();
        } else {
            addMessage('ai', '❌ Error: ' + (data.error || 'Unknown error'));
        }
    } catch (e) {
        hideTyping();
        stopThoughtTimer();
        addMessage('ai', '❌ Network error: ' + e.message);
        updateThoughtStep(1, 'failed', { error: e.message });
    }
}

// ============ UI HELPERS ============
function addMessage(type, content, isLoading = false) {
    const container = document.getElementById('chat-messages');
    if (!container) return;
    
    const div = document.createElement('div');
    const id = isLoading ? 'loading-' + Date.now() : '';
    if (id) div.id = id;
    
    div.className = `message ${type}`;
    div.style.cssText = `
        padding: 12px;
        background: ${type === 'user' ? '#1e293b' : '#0f172a'};
        border: 1px solid ${type === 'user' ? '#38bdf8' : '#334155'};
        border-radius: 8px;
        margin-bottom: 10px;
        max-width: 85%;
        ${type === 'user' ? 'margin-left: auto;' : ''}
        white-space: pre-wrap;
        word-wrap: break-word;
    `;
    
    div.textContent = content;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    
    return id;
}

function showTyping() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.style.display = 'block';
}

function hideTyping() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.style.display = 'none';
}

function clearChat() {
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = '<div class="message ai" style="padding: 12px; background: #1e293b; border-radius: 8px; margin-bottom: 10px; max-width: 80%;">👋 Chat cleared. Ask me anything!</div>';
    }
    clearThoughtProcess();
}

function renameSession() {
    if (!currentSessionId) return;
    const newTitle = prompt('Enter new session name:', document.getElementById('current-session-title')?.textContent || 'Chat');
    if (!newTitle) return;
    fetch('/api/v1/chat/sessions/' + currentSessionId, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle })
    })
    .then(res => res.json())
    .then(() => {
        const titleEl = document.getElementById('current-session-title');
        if (titleEl) titleEl.textContent = newTitle;
        showToast('Session renamed', 'success');
        loadSessions();
    })
    .catch(() => showToast('Error renaming session', 'error'));
}

function deleteCurrentSession() {
    if (!currentSessionId) return;
    if (!confirm('Delete this session?')) return;
    fetch('/api/v1/chat/sessions/' + currentSessionId, { method: 'DELETE' })
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
        showToast('Session deleted', 'info');
    })
    .catch(() => showToast('Error deleting session', 'error'));
}

console.log('✅ chat.js loaded - Chat functions available globally');
