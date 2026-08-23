// ============================================================
// MODEL MANAGEMENT - Complete Version
// ============================================================

console.log('📦 Model Management JS loading...');

// ============ FETCH INSTALLED MODELS ============
async function fetchInstalledModels() {
    const list = document.getElementById('models-list');
    if (!list) {
        console.warn('models-list not found');
        return;
    }
    
    list.innerHTML = '<div class="metric-label">Loading models...</div>';
    try {
        const res = await fetch('/api/v1/admin/dashboard/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        const data = await res.json();
        console.log("DEBUG: Models API Response:", data);
        const activeModel = data.active_model || 'tinydolphin:latest';
        
        if (data.models && data.models.length > 0) {
            list.innerHTML = data.models.map(m => {
                const baseName = m.name.split(':')[0];
                const activeBase = activeModel ? activeModel.split(':')[0] : '';
                const isActive = baseName === activeBase;
                return `
                    <div style="display:flex; justify-content:space-between; padding:12px; background:${isActive ? 'rgba(56, 189, 248, 0.05)' : '#020617'}; border-radius:8px; border:1px solid ${isActive ? '#38bdf8' : '#334155'}; align-items:center; margin-bottom:8px;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <div>
                                <div style="font-weight:700;color:${isActive ? '#38bdf8' : '#94a3b8'};">${m.name}</div>
                                <div style="font-size:11px;color:#64748b;">Size: ${(m.size/(1024*1024*1024)).toFixed(2)} GB</div>
                            </div>
                            ${isActive ? '<span class="tag tag-success" style="font-size:9px; padding:2px 6px;">ACTIVE</span>' : ''}
                        </div>
                        <div style="display:flex; gap:8px;">
                            ${!isActive ? `<button class="btn btn-sm" style="color:#38bdf8;border-color:#38bdf8;padding:4px 10px;font-size:11px;background:#1e293b;border:1px solid #38bdf8;border-radius:4px;cursor:pointer;" onclick="setActiveModel('${m.name}')">Use Model</button>` : ''}
                            <button class="btn btn-sm" style="color:#f87171;border-color:#f87171;padding:4px 10px;font-size:11px;background:#1e293b;border:1px solid #f87171;border-radius:4px;cursor:pointer;" onclick="deleteModel('${m.name}')">Delete</button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            list.innerHTML = '<div class="metric-label">No models installed</div>';
        }
    } catch (e) { 
        console.error('Error loading models:', e);
        list.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading models</div>'; 
    }
}

// ============ SET ACTIVE MODEL ============
async function setActiveModel(name) {
    try {
        showToast('Switching model to ' + name + '...', 'info');
        const res = await fetch('/api/v1/admin/models/set-active', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: name })
        });
        if (res.ok) {
            showToast('Model switched to ' + name, 'success');
            fetchInstalledModels();
            fetchPrimaryAIProvider();
        } else {
            throw new Error('Failed to switch model');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

// ============ DELETE MODEL ============
async function deleteModel(name) {
    if (!confirm('Delete ' + name + '?')) return;
    try {
        await fetch(`/api/v1/admin/dashboard/models/${name}`, {method: 'DELETE'});
        showToast('Deleted ' + name, 'info');
        fetchInstalledModels();
    } catch (e) { 
        showToast('Delete failed: ' + e.message, 'error'); 
    }
}

// ============ TRIGGER MODEL PULL ============
async function triggerModelPull() {
    const input = document.getElementById('new-model-input');
    const statusDiv = document.getElementById('pull-status');
    const statusLabel = document.getElementById('pull-status-label');
    const progressBar = document.getElementById('pull-progress-bar');
    const progressPct = document.getElementById('pull-percentage');
    const progressContainer = document.getElementById('pull-progress-container');
    
    const name = input?.value?.trim();
    if (!name) { showToast('Enter a model name', 'error'); return; }
    
    if (progressContainer) progressContainer.style.display = 'block';
    if (progressBar) progressBar.style.width = '0%';
    if (progressPct) progressPct.textContent = '0%';
    if (statusLabel) statusLabel.textContent = 'Pulling ' + name + '...';
    if (statusDiv) { statusDiv.textContent = ''; statusDiv.style.display = 'none'; }
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/models/pull', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name})
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to start pull');
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const {value, done} = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, {stream: true});
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const data = JSON.parse(line);
                    if (data.error) throw new Error(data.error);
                    if (data.status) {
                        statusLabel.textContent = data.status;
                        if (statusDiv) {
                            statusDiv.style.display = 'block';
                            statusDiv.textContent += data.status + '\n';
                            statusDiv.scrollTop = statusDiv.scrollHeight;
                        }
                    }
                    if (data.total && data.completed) {
                        const percent = Math.round((data.completed / data.total) * 100);
                        if (progressBar) progressBar.style.width = percent + '%';
                        if (progressPct) progressPct.textContent = percent + '%';
                    }
                    if (data.status === 'success') {
                        showToast(name + ' pulled successfully', 'success');
                        setTimeout(() => {
                            if (progressContainer) progressContainer.style.display = 'none';
                            fetchInstalledModels();
                        }, 2000);
                    }
                } catch (e) {
                    console.warn('Failed to parse pull status chunk:', line, e);
                }
            }
        }
    } catch (e) {
        if (statusLabel) statusLabel.textContent = '❌ Error: ' + e.message;
        if (statusDiv) statusDiv.style.display = 'block';
        showToast('Pull failed: ' + e.message, 'error');
    }
}

// ============ FETCH PRIMARY AI PROVIDER ============
async function fetchPrimaryAIProvider() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        console.log("DEBUG: Primary AI Provider:", data);
        
        const status = document.getElementById('primary-ai-provider-status');
        if (status) {
            status.textContent = data.primary_provider || 'ollama';
            status.className = 'tag tag-info';
        }
        const chatStatus = document.getElementById('primary-ai-provider-status-chat');
        if (chatStatus) {
            chatStatus.textContent = data.primary_provider || 'ollama';
            chatStatus.className = 'tag tag-info';
        }
        return data.primary_provider || 'ollama';
    } catch (e) {
        console.error('Error fetching primary AI provider:', e);
        ['primary-ai-provider-status', 'primary-ai-provider-status-chat'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = 'ollama';
                el.className = 'tag tag-info';
            }
        });
        return 'ollama';
    }
}

// ============ UPDATE PRIMARY AI PROVIDER ============
window.updatePrimaryAIProvider = async function(value) {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: value })
        });
        if (!res.ok) throw new Error('Failed to update provider');
        showToast(`✅ Primary provider set to ${value}`, 'success');
        await fetchPrimaryAIProvider();
        // Update context bar
        const contextEl = document.getElementById('context-provider');
        if (contextEl) contextEl.textContent = value;
        // Update chat dropdown
        const chatSelect = document.getElementById('chat-provider-select');
        if (chatSelect) chatSelect.value = value;
        return true;
    } catch (e) {
        console.error('Error updating provider:', e);
        showToast('Error: ' + e.message, 'error');
        return false;
    }
};

// ============ FETCH CLOUD CONNECTIONS ============
async function fetchCloudConnections() {
    const list = document.getElementById('cloud-connections-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-providers/cloud');
        if (!res.ok) throw new Error('Failed to fetch cloud connections');
        const data = await res.json();
        console.log('📋 Cloud connections:', data);
        
        if (data && data.length > 0) {
            list.innerHTML = data.map(p => `
                <div style="background: #1e293b; padding: 12px; border-radius: 6px; border: 1px solid #334155; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-weight: 600; color: #f1f5f9;">${p.name}</span>
                        ${p.name === 'groq' ? ' <span class="tag tag-info">Primary</span>' : ''}
                        <div style="font-size: 11px; color: #94a3b8;">Model: ${p.model || 'Default'} | Host: ${p.host || 'Local'}</div>
                    </div>
                    <div style="display: flex; gap: 6px;">
                        <span class="tag ${p.enabled !== false ? 'tag-success' : 'tag-danger'}">${p.enabled !== false ? '✅ Active' : '⏸️ Disabled'}</span>
                        <button class="btn btn-sm" style="background: #1e293b; padding: 2px 10px; font-size: 10px;" onclick="fetchAIProviderSettings('${p.name}')">✏️ Edit</button>
                        <button class="btn btn-sm" style="background: #f87171; padding: 2px 10px; font-size: 10px;" onclick="deleteCloudConfig('${p.name}')">🗑️ Delete</button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<div class="metric-label" style="padding: 20px; text-align: center; color: #64748b;">No cloud connections configured.</div>';
        }
    } catch (e) {
        console.error('Error fetching cloud connections:', e);
        list.innerHTML = '<div style="color: #f87171; padding: 20px; text-align: center;">Error loading providers: ' + e.message + '</div>';
    }
}

// ============ INITIALIZE ============
document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 DOM loaded, checking for models tab...');
    const modelsTab = document.querySelector('[data-tab="models"]');
    if (modelsTab && modelsTab.classList.contains('active')) {
        console.log('📦 Models tab active, initializing...');
        fetchInstalledModels();
        fetchPrimaryAIProvider();
        fetchCloudConnections();
    }
});

// Make functions globally accessible
window.fetchInstalledModels = fetchInstalledModels;
window.setActiveModel = setActiveModel;
window.deleteModel = deleteModel;
window.triggerModelPull = triggerModelPull;
window.fetchPrimaryAIProvider = fetchPrimaryAIProvider;
window.fetchCloudConnections = fetchCloudConnections;

console.log('✅ Model Management JS loaded');
