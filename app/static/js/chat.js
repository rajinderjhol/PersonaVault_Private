// ============================================================
// CHAT FUNCTIONS - Complete chat UI
// ============================================================

// ============ FETCH HELPER ============
function getFetchOptions(method = 'GET', body = null) {
    const options = {
        method: method,
        credentials: 'include',  // Sends HTTP-only cookies automatically
        headers: {
            'Content-Type': 'application/json'
        }
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    return options;
}

let currentSessionId = null;
let thoughtSteps = [];
let thoughtTimer = null;
let thoughtStartTime = null;

// ============ THOUGHT PROCESS TOGGLE ============
function toggleThoughtProcess() {
    let container = document.getElementById('thought-process-container');
    let toggleBtn = document.querySelector('[onclick="toggleThoughtProcess()"]');
    
    if (!container) {
        const chatContainer = document.getElementById('chat-container') || document.body;
        container = document.createElement('div');
        container.id = 'thought-process-container';
        container.style.cssText = 'margin-top: 10px; display: block;';
        
        const thoughtProcess = document.createElement('div');
        thoughtProcess.id = 'thought-process';
        thoughtProcess.style.cssText = 'max-height: 200px; overflow-y: auto; padding: 8px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 12px; color: #94a3b8;';
        container.appendChild(thoughtProcess);
        
        const statusEl = document.createElement('div');
        statusEl.id = 'thought-status';
        statusEl.style.cssText = 'font-size: 11px; color: #64748b; margin-top: 4px;';
        container.appendChild(statusEl);
        
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages && chatMessages.parentElement) {
            chatMessages.parentElement.insertBefore(container, chatMessages.nextSibling);
        } else {
            chatContainer.appendChild(container);
        }
        
        if (!toggleBtn) {
            toggleBtn = document.createElement('button');
            toggleBtn.textContent = '▼ Hide Thought Process';
            toggleBtn.setAttribute('onclick', 'toggleThoughtProcess()');
            toggleBtn.style.cssText = 'margin: 5px 0; padding: 4px 12px; background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 4px; cursor: pointer; font-size: 12px;';
            container.parentElement.insertBefore(toggleBtn, container);
        }
        return;
    }
    
    if (toggleBtn && toggleBtn.parentElement === container) {
        const parent = container.parentElement;
        if (parent) {
            const newBtn = document.createElement('button');
            newBtn.textContent = container.style.display === 'none' ? '▶ Show Thought Process' : '▼ Hide Thought Process';
            newBtn.setAttribute('onclick', 'toggleThoughtProcess()');
            newBtn.style.cssText = 'margin: 5px 0; padding: 4px 12px; background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 4px; cursor: pointer; font-size: 12px;';
            parent.insertBefore(newBtn, container);
            toggleBtn.remove();
            toggleBtn = newBtn;
        }
    }
    
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        if (toggleBtn) toggleBtn.textContent = '▼ Hide Thought Process';
    } else {
        container.style.display = 'none';
        if (toggleBtn) toggleBtn.textContent = '▶ Show Thought Process';
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

// ============ SESSION PINNING ============
async function togglePinSession(sessionId) {
    try {
        const res = await fetch(`/api/v1/chat/sessions/${sessionId}/pin`, 
            getFetchOptions('PATCH', { pinned: true })
        );
        if (res.ok) {
            await loadSessions();
            showToast('Session pinned! 📌', 'success');
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
        }
    } catch (e) {
        console.error('Error unpinning session:', e);
        showToast('Error unpinning session', 'error');
    }
}

// ============ SESSIONS ============
async function loadSessions() {
    const list = document.getElementById('session-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/v1/chat/sessions', getFetchOptions());
        if (!res.ok) throw new Error('Failed to load sessions');
        let sessions = await res.json();
        
        // Sort: pinned first, then by updated_at
        sessions.sort((a, b) => {
            if (a.pinned && !b.pinned) return -1;
            if (!a.pinned && b.pinned) return 1;
            return new Date(b.updated_at) - new Date(a.updated_at);
        });
        
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
                            border: 1px solid ${isActive ? '#38bdf8' : 'transparent'};
                            ${s.pinned ? 'border-left: 3px solid #fbbf24;' : ''}
                            display: flex; flex-direction: column; gap: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="session-title" style="color: #f1f5f9; font-size: 13px; font-weight: ${isActive ? '600' : '400'};">
                            ${s.pinned ? '📌 ' : ''}${s.title || 'Untitled Chat'}
                        </span>
                        <span style="font-size: 10px; color: #64748b;">${new Date(s.updated_at).toLocaleDateString()}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 10px; color: #64748b;">${s.message_count || 0} messages</span>
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

// ============ CREATE SESSION ============
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

// ============ LOAD SESSION ============
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
    } catch (e) {
        console.error('Error loading session:', e);
        showToast('Error loading session', 'error');
    }
}

// ============ SEND MESSAGE ============
async function sendMessage() {
    const input = document.getElementById('chat-input');
    if (!input) return;
    const query = input.value.trim();
    if (!query) return;
    input.value = '';
    await sendChatMessage(query);
}

// ============ STREAMING CHAT ============
async function sendChatMessageStream() {
    const input = document.getElementById('chat-input');
    if (!input) {
        const altInput = document.getElementById('message-input') || document.getElementById('input-message');
        if (altInput) {
            const message = altInput.value.trim();
            if (!message) return;
            altInput.value = '';
            await sendChatMessage(message);
            return;
        }
        console.error('Chat input not found');
        return;
    }
    
    const message = input.value.trim();
    if (!message) return;
    input.value = '';
    await sendChatMessage(message);
}

// ============ QUICK PROMPTS ============
function sendQuickPrompt(prompt) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = prompt;
        sendChatMessageStream();
    }
}

// ============ CORE CHAT FUNCTION ============
async function sendChatMessage(query) {
    const providerSelect = document.getElementById('chat-provider');
    const provider = providerSelect ? providerSelect.value : 'groq';
    
    const container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML += `
            <div class="message user" 
                 style="padding: 12px; background: #1e293b; border: 1px solid #38bdf8; 
                        border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                        margin-left: auto; white-space: pre-wrap; word-wrap: break-word;">
                ${query}
            </div>
        `;
        container.scrollTop = container.scrollHeight;
    }
    
    showTyping();
    startThoughtTimer();
    addThoughtStep({ step: 1, label: 'Initializing', description: 'Processing your request...', status: 'active' });
    
    try {
        const res = await fetch('/api/v1/chat', 
            getFetchOptions('POST', {
                query: query,
                provider: provider,
                session_id: currentSessionId,
                track_thoughts: true
            })
        );
        
        if (res.status === 401) {
            hideTyping();
            stopThoughtTimer();
            showToast('Session expired. Please refresh the page.', 'error');
            if (container) {
                container.innerHTML += `
                    <div class="message ai" 
                         style="padding: 12px; background: #1a0f0f; border: 1px solid #f87171; 
                                border-radius: 8px; margin-bottom: 10px; max-width: 85%;">
                        ⚠️ Session expired. Please refresh the page to continue.
                    </div>
                `;
            }
            return;
        }
        
        if (!res.ok) throw new Error('Failed to send message');
        
        const data = await res.json();
        hideTyping();
        stopThoughtTimer();
        
        if (data.thought_process && data.thought_process.length > 0) {
            const firstStep = data.thought_process[0];
            if (firstStep) {
                updateThoughtStep(1, firstStep.status || 'complete', firstStep.data);
            }
            for (let i = 1; i < data.thought_process.length; i++) {
                const step = data.thought_process[i];
                addThoughtStep({
                    step: step.step || i + 1,
                    label: step.label || 'Step',
                    description: step.description || '',
                    status: step.status || 'complete',
                    duration: step.duration || 0,
                    data: step.data || {}
                });
            }
            setTimeout(() => {
                completeAllThoughtSteps();
            }, 500);
        } else {
            setTimeout(() => {
                completeAllThoughtSteps();
            }, 300);
        }
        
        if (container && data.response) {
            container.innerHTML += `
                <div class="message ai" 
                     style="padding: 12px; background: #0f172a; border: 1px solid #334155; 
                            border-radius: 8px; margin-bottom: 10px; max-width: 85%; 
                            white-space: pre-wrap; word-wrap: break-word;">
                    ${data.response}
                    ${data.provider ? `<div style="font-size: 10px; color: #64748b; margin-top: 4px;">⚡ ${data.provider}</div>` : ''}
                    <div style="margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <button onclick="copyMessageContent(this)" style="background: #1e293b; border: none; color: #94a3b8; padding: 2px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">📋 Copy</button>
                        <button onclick="shareMessage(this)" style="background: #1e293b; border: none; color: #94a3b8; padding: 2px 10px; border-radius: 4px; cursor: pointer; font-size: 11px;">🔗 Share</button>
                    </div>
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }
        
        if (data.session_id) {
            currentSessionId = data.session_id;
            const idEl = document.getElementById('session-id-display');
            if (idEl) idEl.textContent = '#' + data.session_id;
            await loadSessions();
        }
        
    } catch (e) {
        console.error('Chat error:', e);
        hideTyping();
        stopThoughtTimer();
        if (container) {
            container.innerHTML += `
                <div class="message ai" 
                     style="padding: 12px; background: #1a0f0f; border: 1px solid #f87171; 
                            border-radius: 8px; margin-bottom: 10px; max-width: 85%;">
                    ❌ Error: ${e.message || 'Failed to send message'}
                </div>
            `;
            container.scrollTop = container.scrollHeight;
        }
        showToast('Error sending message', 'error');
    }
}

// ============ COPY & SHARE ============
function copyMessageContent(btn) {
    const messageDiv = btn.closest('.message.ai');
    const content = messageDiv?.textContent?.replace('📋 Copy', '').replace('🔗 Share', '').trim() || '';
    navigator.clipboard.writeText(content).then(() => {
        btn.textContent = '✅ Copied!';
        setTimeout(() => btn.textContent = '📋 Copy', 2000);
    });
}

function shareMessage(btn) {
    const messageDiv = btn.closest('.message.ai');
    const content = messageDiv?.textContent?.replace('📋 Copy', '').replace('🔗 Share', '').trim() || '';
    if (navigator.share) {
        navigator.share({
            title: 'PersonaVault Chat',
            text: content,
        }).catch(() => {});
    } else {
        navigator.clipboard.writeText(content).then(() => {
            showToast('Message copied to clipboard! 📋', 'success');
        });
    }
}

// ============ RENAME SESSION ============
function renameSession(newTitle) {
    if (!currentSessionId || !newTitle) return;
    
    fetch('/api/v1/chat/sessions/' + currentSessionId, 
        getFetchOptions('PATCH', { title: newTitle })
    )
    .then(res => res.json())
    .then(() => {
        const titleEl = document.getElementById('current-session-title');
        if (titleEl) titleEl.textContent = newTitle;
        showToast('Session renamed', 'success');
        loadSessions();
    })
    .catch(() => showToast('Error renaming session', 'error'));
}

// ============ DELETE SESSION ============
function deleteCurrentSession() {
    if (!currentSessionId) return;
    if (!confirm('Delete this session?')) return;
    
    fetch('/api/v1/chat/sessions/' + currentSessionId, 
        getFetchOptions('DELETE')
    )
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

// ============ THOUGHT PROCESS UI ============
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
    let container = document.getElementById('thought-process');
    if (!container) {
        let parentContainer = document.getElementById('thought-process-container');
        if (!parentContainer) {
            const chatContainer = document.getElementById('chat-container') || document.body;
            parentContainer = document.createElement('div');
            parentContainer.id = 'thought-process-container';
            parentContainer.style.cssText = 'margin-top: 10px; display: block;';
            
            container = document.createElement('div');
            container.id = 'thought-process';
            container.style.cssText = 'max-height: 200px; overflow-y: auto; padding: 8px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 12px; color: #94a3b8;';
            parentContainer.appendChild(container);
            
            const statusEl = document.createElement('div');
            statusEl.id = 'thought-status';
            statusEl.style.cssText = 'font-size: 11px; color: #64748b; margin-top: 4px;';
            parentContainer.appendChild(statusEl);
            
            const chatMessages = document.getElementById('chat-messages');
            if (chatMessages && chatMessages.parentElement) {
                chatMessages.parentElement.insertBefore(parentContainer, chatMessages.nextSibling);
            } else {
                chatContainer.appendChild(parentContainer);
            }
            
            if (!document.querySelector('[onclick="toggleThoughtProcess()"]')) {
                const toggleBtn = document.createElement('button');
                toggleBtn.textContent = '▼ Hide Thought Process';
                toggleBtn.setAttribute('onclick', 'toggleThoughtProcess()');
                toggleBtn.style.cssText = 'margin: 5px 0; padding: 4px 12px; background: #1e293b; color: #f1f5f9; border: 1px solid #334155; border-radius: 4px; cursor: pointer; font-size: 12px;';
                parentContainer.parentElement.insertBefore(toggleBtn, parentContainer);
            }
        } else {
            container = document.getElementById('thought-process');
            if (!container) {
                container = document.createElement('div');
                container.id = 'thought-process';
                container.style.cssText = 'max-height: 200px; overflow-y: auto; padding: 8px; background: #0f172a; border-radius: 8px; border: 1px solid #334155; font-size: 12px; color: #94a3b8;';
                parentContainer.insertBefore(container, parentContainer.firstChild);
            }
        }
    }
    
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
    
    const parentContainer = document.getElementById('thought-process-container');
    if (parentContainer) {
        parentContainer.style.display = 'block';
        const toggleBtn = document.querySelector('[onclick="toggleThoughtProcess()"]');
        if (toggleBtn) {
            toggleBtn.textContent = '▼ Hide Thought Process';
        }
    }
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
    const statusEl = document.getElementById('thought-status');
    if (statusEl) {
        statusEl.textContent = '';
    }
    stopThoughtTimer();
    
    const parentContainer = document.getElementById('thought-process-container');
    if (parentContainer) {
        parentContainer.style.display = 'none';
        const toggleBtn = document.querySelector('[onclick="toggleThoughtProcess()"]');
        if (toggleBtn) {
            toggleBtn.textContent = '▶ Show Thought Process';
        }
    }
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
    container.scrollTop = container.scrollHeight;
}

function hideTyping() {
    const typingEl = document.getElementById('typing-indicator');
    if (typingEl) {
        typingEl.remove();
    }
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

// ============ KEYBOARD SHORTCUTS ============
document.addEventListener('DOMContentLoaded', function() {
    const input = document.getElementById('chat-input');
    if (input) {
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendChatMessageStream();
            }
        });
    }
    
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

// Add CSS animation
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
`;
document.head.appendChild(style);

console.log('✅ chat.js loaded - Chat functions available globally');
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
    
    // Show "no results" message
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

// ============ QUICK PROMPTS ============
function sendQuickPrompt(prompt) {
    const input = document.getElementById('chat-input');
    if (input) {
        input.value = prompt;
        sendChatMessageStream();
    }
}
