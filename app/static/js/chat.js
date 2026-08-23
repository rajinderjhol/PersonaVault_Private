// ============================================================
// CHAT FUNCTIONS - Clean Version
// ============================================================

console.log('📡 Chat.js loading...');

// ============ CONFIGURATION ============
let currentSessionId = null;
let currentSessionTitle = '';
let autoScroll = true;
let _lastThoughtProcess = null;

// ============ TOAST ============
function showToast(message, type) {
    type = type || 'info';
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const bgColor = type === 'error' ? '#991b1b' : type === 'success' ? '#14532d' : '#1e293b';
    const borderColor = type === 'error' ? '#f87171' : type === 'success' ? '#22c55e' : '#334155';
    toast.style.cssText = 'padding:12px 20px;border-radius:8px;background:' + bgColor + ';color:#f1f5f9;border:1px solid ' + borderColor + ';box-shadow:0 4px 6px rgba(0,0,0,0.3);min-width:200px;font-size:14px;';
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(function() {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(function() { toast.remove(); }, 300);
    }, 3000);
}

// ============ PROVIDER ============
async function getPrimaryProvider() {
    try {
        var res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (res.ok) {
            var data = await res.json();
            return data.primary_provider || 'ollama';
        }
    } catch (e) {}
    return 'ollama';
}

async function loadProviderIntoUI() {
    var provider = await getPrimaryProvider();
    var select = document.getElementById('chat-provider-select');
    if (select) select.value = provider;
    var status = document.getElementById('primary-ai-provider-status-chat');
    if (status) {
        status.textContent = provider;
        status.className = 'tag tag-info';
    }
}

// ============ SESSIONS ============
async function loadSessions() {
    var container = document.getElementById('session-list');
    if (!container) return;
    try {
        var res = await fetch('/api/v1/chat/sessions');
        if (!res.ok) throw new Error('Failed to load sessions');
        var sessions = await res.json();
        if (sessions.length === 0) {
            container.innerHTML = '<div style="padding:20px;text-align:center;color:#64748b;">No sessions yet.<br>Click "New" to start chatting!</div>';
            return;
        }
        var html = '';
        for (var i = 0; i < sessions.length; i++) {
            var s = sessions[i];
            var isActive = s.id === currentSessionId;
            var msgCount = s.message_count || 0;
            var title = s.title || 'Untitled Chat';
            var date = new Date(s.updated_at || s.created_at).toLocaleDateString();
            html += '<div onclick="loadSession(' + s.id + ')" style="padding:10px;margin-bottom:6px;border-radius:6px;cursor:pointer;background:' + (isActive ? 'rgba(56,189,248,0.1)' : 'transparent') + ';border:1px solid ' + (isActive ? '#38bdf8' : 'transparent') + ';">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<span style="color:' + (isActive ? '#38bdf8' : '#f1f5f9') + ';font-size:13px;font-weight:' + (isActive ? '600' : '400') + ';">' + title + '</span>';
            html += '<span style="font-size:10px;color:#64748b;">' + date + '</span>';
            html += '</div>';
            html += '<div style="display:flex;justify-content:space-between;margin-top:4px;">';
            html += '<span style="font-size:10px;color:#64748b;">💬 ' + msgCount + ' messages</span>';
            html += '<div style="display:flex;gap:6px;">';
            html += '<button onclick="event.stopPropagation();renameSessionDirect(' + s.id + ')" style="background:none;border:none;color:#94a3b8;cursor:pointer;font-size:10px;">✏️</button>';
            html += '<button onclick="event.stopPropagation();deleteSession(' + s.id + ')" style="background:none;border:none;color:#f87171;cursor:pointer;font-size:10px;">🗑️</button>';
            html += '</div></div></div>';
        }
        container.innerHTML = html;
    } catch (e) {
        console.error('Error loading sessions:', e);
        container.innerHTML = '<div style="color:#f87171;padding:20px;text-align:center;">Error loading sessions</div>';
    }
}

async function createNewSession() {
    try {
        var res = await fetch('/api/v1/chat/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'New Chat' })
        });
        if (!res.ok) throw new Error('Failed to create session');
        var data = await res.json();
        currentSessionId = data.id;
        currentSessionTitle = data.title || 'New Chat';
        document.getElementById('current-session-title').textContent = currentSessionTitle;
        document.getElementById('session-id-display').textContent = '#' + data.id;
        clearChat();
        await loadSessions();
        showToast('✅ New chat session created!', 'success');
        return data.id;
    } catch (e) {
        showToast('Error creating session: ' + e.message, 'error');
        return null;
    }
}

async function loadSession(sessionId) {
    currentSessionId = sessionId;
    try {
        var res = await fetch('/api/v1/chat/sessions/' + sessionId + '/messages');
        if (!res.ok) throw new Error('Failed to load messages');
        var data = await res.json();
        currentSessionTitle = data.title || 'Chat';
        document.getElementById('current-session-title').textContent = currentSessionTitle;
        document.getElementById('session-id-display').textContent = '#' + sessionId;
        var container = document.getElementById('chat-messages');
        if (container) {
            if (data.messages && data.messages.length > 0) {
                var html = '';
                for (var i = 0; i < data.messages.length; i++) {
                    var m = data.messages[i];
                    html += '<div class="message ' + m.role + '" style="padding:12px;background:' + (m.role === 'user' ? '#1e293b' : '#0f172a') + ';border:1px solid ' + (m.role === 'user' ? '#38bdf8' : '#334155') + ';border-radius:8px;margin-bottom:10px;max-width:85%;' + (m.role === 'user' ? 'margin-left:auto;' : '') + 'white-space:pre-wrap;word-wrap:break-word;">';
                    html += m.content;
                    if (m.provider) html += '<div style="font-size:10px;color:#64748b;margin-top:4px;">⚡ ' + m.provider + '</div>';
                    html += '</div>';
                }
                container.innerHTML = html;
                container.scrollTop = container.scrollHeight;
            } else {
                container.innerHTML = '<div class="message ai" style="padding:12px;background:#1e293b;border-radius:8px;margin-bottom:10px;max-width:80%;">👋 Continue your conversation here.</div>';
            }
        }
        await loadSessions();
    } catch (e) {
        showToast('Error loading session: ' + e.message, 'error');
    }
}

async function renameSessionDirect(sessionId, newTitle) {
    if (!newTitle) {
        newTitle = prompt('Enter new session name:', '');
        if (!newTitle) return;
    }
    try {
        var res = await fetch('/api/v1/chat/sessions/' + sessionId, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: newTitle })
        });
        if (!res.ok) throw new Error('Failed to rename session');
        if (sessionId === currentSessionId) {
            currentSessionTitle = newTitle;
            document.getElementById('current-session-title').textContent = newTitle;
        }
        await loadSessions();
        showToast('✅ Session renamed!', 'success');
    } catch (e) {
        showToast('Error renaming session: ' + e.message, 'error');
    }
}

async function deleteSession(sessionId) {
    if (!confirm('Delete this session?')) return;
    try {
        var res = await fetch('/api/v1/chat/sessions/' + sessionId, { method: 'DELETE' });
        if (!res.ok) throw new Error('Failed to delete session');
        if (sessionId === currentSessionId) {
            currentSessionId = null;
            document.getElementById('current-session-title').textContent = 'New Chat';
            document.getElementById('session-id-display').textContent = '';
            clearChat();
        }
        await loadSessions();
        showToast('🗑️ Session deleted', 'info');
    } catch (e) {
        showToast('Error deleting session: ' + e.message, 'error');
    }
}

function refreshSessions() { loadSessions(); }

function searchSessions(query) {
    var items = document.querySelectorAll('.session-item');
    var searchTerm = query.toLowerCase().trim();
    items.forEach(function(item) {
        var title = item.querySelector('span:first-child')?.textContent?.toLowerCase() || '';
        item.style.display = title.includes(searchTerm) ? '' : 'none';
    });
}

function clearChat() {
    var container = document.getElementById('chat-messages');
    if (container) {
        container.innerHTML = '<div class="message ai" style="padding:12px;background:#1e293b;border-radius:8px;margin-bottom:10px;max-width:80%;">👋 Start a new conversation or select a session.</div>';
    }
}

// ============ THOUGHT PROCESS ============
function toggleThoughtProcess() {
    var container = document.getElementById('thought-steps');
    var label = document.getElementById('thought-toggle-label');
    if (!container) return;
    if (container.style.display === 'none' || container.style.display === '') {
        container.style.display = 'block';
        if (label) label.textContent = 'Hide';
    } else {
        container.style.display = 'none';
        if (label) label.textContent = 'Show';
    }
}

function updateThoughtProcessUI(thoughtSteps) {
    var container = document.getElementById('thought-steps-container');
    if (!container || !thoughtSteps || thoughtSteps.length === 0) return;
    var lastStep = thoughtSteps[thoughtSteps.length - 1];
    var stepNum = lastStep.step || '';
    var label = lastStep.label || 'Processing...';
    var desc = lastStep.description || '';
    var status = lastStep.status || 'in-progress';
    var statusColor = status === 'complete' ? '#34d399' : status === 'in-progress' ? '#fbbf24' : '#f87171';
    container.innerHTML = '';
    var div = document.createElement('div');
    div.style.cssText = 'padding:8px 0;border-bottom:1px solid #1e293b;';
    div.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;"><span style="font-weight:600;color:#38bdf8;">' + stepNum + ' ' + label + '</span><span style="font-size:10px;color:' + statusColor + ';">' + status + '</span></div>';
    if (desc) div.innerHTML += '<div style="color:#94a3b8;font-size:11px;margin-left:24px;margin-top:2px;">' + desc + '</div>';
    container.appendChild(div);
    var steps = document.getElementById('thought-steps');
    if (steps) { steps.style.display = 'block'; }
    var toggleLabel = document.getElementById('thought-toggle-label');
    if (toggleLabel) toggleLabel.textContent = 'Hide';
    _lastThoughtProcess = thoughtSteps;
}

// ============ SEND MESSAGE ============
async function sendChatMessageStream() {
    var input = document.getElementById('chat-input');
    var query = input?.value?.trim();
    if (!query) return;
    var provider = document.getElementById('chat-provider-select')?.value || 'groq';
    var container = document.getElementById('chat-messages');
    if (!container) return;
    container.innerHTML += '<div class="message user" style="padding:12px;background:#1e293b;border:1px solid #38bdf8;border-radius:8px;margin-bottom:10px;max-width:85%;margin-left:auto;white-space:pre-wrap;word-wrap:break-word;">' + query + '</div>';
    if (autoScroll) container.scrollTop = container.scrollHeight;
    input.value = '';
    if (!currentSessionId) { await createNewSession(); }
    var typingEl = document.createElement('div');
    typingEl.id = 'typing-indicator';
    typingEl.style.cssText = 'padding:12px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:10px;max-width:85%;color:#94a3b8;';
    typingEl.textContent = '⏳ Thinking...';
    container.appendChild(typingEl);
    if (autoScroll) container.scrollTop = container.scrollHeight;
    try {
        var requestBody = { query: query, provider: provider, track_thoughts: true, session_id: currentSessionId };
        var response = await fetch('/api/v1/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(requestBody)
        });
        if (!response.ok) throw new Error('Server error: ' + response.status);
        var messageDiv = document.createElement('div');
        messageDiv.className = 'message ai';
        messageDiv.style.cssText = 'padding:16px;background:#0f172a;border:1px solid #334155;border-radius:8px;margin-bottom:10px;max-width:85%;white-space:pre-wrap;word-wrap:break-word;';
        var contentDiv = document.createElement('div');
        contentDiv.style.cssText = 'color:#e2e8f0;font-size:14px;line-height:1.6;min-height:20px;';
        contentDiv.textContent = '▍';
        messageDiv.appendChild(contentDiv);
        container.appendChild(messageDiv);
        if (autoScroll) container.scrollTop = container.scrollHeight;
        var typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) typingIndicator.remove();
        var reader = response.body.getReader();
        var decoder = new TextDecoder();
        var fullContent = '';
        var buffer = '';
        while (true) {
            var result = await reader.read();
            if (result.done) break;
            buffer += decoder.decode(result.value, { stream: true });
            var lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (var j = 0; j < lines.length; j++) {
                var line = lines[j].trim();
                if (!line || line.startsWith(':')) continue;
                if (line.startsWith('data: ')) {
                    var dataStr = line.slice(6).trim();
                    if (dataStr === '[DONE]') continue;
                    try {
                        var data = JSON.parse(dataStr);
                        if (data.content) {
                            fullContent += data.content;
                            contentDiv.textContent = fullContent + '▍';
                            if (autoScroll) container.scrollTop = container.scrollHeight;
                        }
                        if (data.thought || data.thought_process) {
                            var steps = data.thought_process || [data.thought];
                            updateThoughtProcessUI(steps);
                        }
                        if (data.session_id) {
                            currentSessionId = data.session_id;
                            document.getElementById('session-id-display').textContent = '#' + data.session_id;
                        }
                    } catch (e) {}
                }
            }
        }
        if (contentDiv) {
            contentDiv.textContent = fullContent;
        }
        await loadSessions();
    } catch (e) {
        console.error('Chat error:', e);
        var typingIndicator2 = document.getElementById('typing-indicator');
        if (typingIndicator2) typingIndicator2.remove();
        showToast('Error: ' + e.message, 'error');
    }
}

function sendQuickPrompt(prompt) {
    var input = document.getElementById('chat-input');
    if (input) { input.value = prompt; sendChatMessageStream(); }
}

// ============ EXPOSE ============
window.sendChatMessageStream = sendChatMessageStream;
window.loadSessions = loadSessions;
window.createNewSession = createNewSession;
window.loadSession = loadSession;
window.renameSessionDirect = renameSessionDirect;
window.deleteSession = deleteSession;
window.refreshSessions = refreshSessions;
window.searchSessions = searchSessions;
window.clearChat = clearChat;
window.toggleThoughtProcess = toggleThoughtProcess;
window.updateThoughtProcessUI = updateThoughtProcessUI;
window.sendQuickPrompt = sendQuickPrompt;
window.showToast = showToast;
window.loadProviderIntoUI = loadProviderIntoUI;
window.getPrimaryProvider = getPrimaryProvider;

// ============ INIT ============
document.addEventListener('DOMContentLoaded', function() {
    console.log('📡 Chat initialized');
    setTimeout(loadSessions, 300);
    loadProviderIntoUI();
    if (!currentSessionId) { setTimeout(createNewSession, 500); }
});

console.log('✅ Chat.js loaded');
