// ============ RELOAD API KEYS ============
async function reloadApiKeys() {
    const statusEl = document.getElementById('reload-status');
    const resultEl = document.getElementById('reload-result');
    
    if (!statusEl) {
        console.warn('Status element not found');
        return;
    }
    
    statusEl.textContent = '⏳ Reloading API keys from .env...';
    statusEl.style.color = '#fbbf24';
    if (resultEl) resultEl.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/reload-api-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        console.log('📊 Reload result:', data);
        
        if (data.status === 'success') {
            statusEl.textContent = '✅ ' + data.message;
            statusEl.style.color = '#34d399';
            
            if (resultEl) {
                resultEl.style.display = 'block';
                resultEl.innerHTML = `
                    <div style="color: #34d399;">✅ Successfully loaded ${data.providers_loaded?.length || 0} provider(s)</div>
                    <div style="color: #94a3b8; margin-top: 4px;">Providers: ${data.providers_loaded?.join(', ') || 'None'}</div>
                    <div style="color: #64748b; margin-top: 4px; font-size: 11px;">Env vars found: ${data.env_vars_found?.join(', ') || 'None'}</div>
                `;
            }
            
            // Refresh the cloud connections list
            fetchCloudConnections();
            if (typeof fetchPrimaryAIProvider === 'function') {
                fetchPrimaryAIProvider();
            }
        } else if (data.status === 'no_keys_found') {
            statusEl.textContent = '⚠️ ' + data.message;
            statusEl.style.color = '#fbbf24';
            if (resultEl) {
                resultEl.style.display = 'block';
                resultEl.innerHTML = `<div style="color: #fbbf24;">⚠️ ${data.message}</div>`;
            }
        } else {
            statusEl.textContent = '❌ Error: ' + (data.error || 'Unknown error');
            statusEl.style.color = '#f87171';
        }
    } catch (e) {
        statusEl.textContent = '❌ Network error: ' + e.message;
        statusEl.style.color = '#f87171';
        console.error('Reload error:', e);
    }
}

// ============ CLOUD CONNECTIONS ============
async function fetchCloudConnections() {
    const list = document.getElementById('cloud-connections-list');
    if (!list) return;
    
    list.innerHTML = '<div class="metric-label">Loading connections...</div>';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-providers/cloud');
        if (!res.ok) throw new Error('Failed to fetch cloud connections');
        const data = await res.json();
        console.log('📋 Cloud connections:', data);
        
        if (data && data.length > 0) {
            list.innerHTML = data.map(p => `
                <div style="display:flex; justify-content:space-between; padding:12px; background:#020617; border-radius:8px; border:1px solid #334155; align-items:center; margin-bottom:10px;">
                    <div style="flex:1;">
                        <div style="font-weight:700; color:#f472b6;">${p.name.charAt(0).toUpperCase() + p.name.slice(1)}</div>
                        <div style="font-size:11px; color:#64748b;">
                            Host: ${p.host || 'Default'} | Model: ${p.model || 'Default'}
                            ${p.enabled ? '<span class="tag tag-success" style="font-size:9px; padding:2px 6px; margin-left:8px;">ACTIVE</span>' : ''}
                        </div>
                        <div style="font-size:10px; color:#64748b; margin-top:2px;">
                            API Key: ${p.api_key ? '••••••••' + p.api_key.slice(-4) : 'Not set'}
                        </div>
                    </div>
                    <div style="display:flex; gap:8px;">
                        <button class="refresh-btn" style="color:#38bdf8; border-color:#38bdf8; padding:4px 10px; font-size:11px;" onclick="editCloudConnection('${p.name}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="refresh-btn" style="color:#f87171; border-color:#f87171; padding:4px 10px; font-size:11px;" onclick="deleteCloudConnection('${p.name}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<div class="metric-label">No cloud connections configured. Add one using the form above.</div>';
        }
    } catch (e) {
        console.error('Error fetching cloud connections:', e);
        list.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading connections: ' + e.message + '</div>';
    }
}

// ============ EDIT CLOUD CONNECTION ============
async function editCloudConnection(name) {
    console.log('✏️ Editing cloud connection:', name);
    try {
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider-settings/${name}`);
        if (!res.ok) throw new Error('Failed to fetch config');
        const data = await res.json();
        console.log('📋 Config data:', data);
        
        // Fill the form
        document.getElementById('cloud-api-name').value = name;
        document.getElementById('cloud-api-host').value = data.host || '';
        document.getElementById('cloud-api-key').value = data.api_key || '';
        document.getElementById('cloud-api-model').value = data.model || '';
        
        // Change the save button to "Update"
        const saveBtn = document.querySelector('#models-tab .card:nth-child(2) .btn:last-child');
        if (saveBtn) {
            saveBtn.textContent = 'Update Connection';
            saveBtn.style.background = '#fbbf24';
            saveBtn.onclick = function() {
                updateCloudConnection(name);
            };
        }
        
        showToast(`Editing ${name} configuration`, 'info');
    } catch (e) {
        console.error('Error editing cloud connection:', e);
        showToast('Error loading configuration: ' + e.message, 'error');
    }
}

// ============ UPDATE CLOUD CONNECTION ============
async function updateCloudConnection(name) {
    const host = document.getElementById('cloud-api-host').value;
    const api_key = document.getElementById('cloud-api-key').value;
    const model = document.getElementById('cloud-api-model').value;
    
    if (!host || !api_key || !model) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: name, host, api_key, model })
        });
        if (!res.ok) throw new Error('Failed to update');
        const data = await res.json();
        
        showToast(`✅ ${name} configuration updated`, 'success');
        
        // Reset form
        document.getElementById('cloud-api-name').value = '';
        document.getElementById('cloud-api-host').value = '';
        document.getElementById('cloud-api-key').value = '';
        document.getElementById('cloud-api-model').value = '';
        
        // Reset button
        const saveBtn = document.querySelector('#models-tab .card:nth-child(2) .btn:last-child');
        if (saveBtn) {
            saveBtn.textContent = 'Save Connection';
            saveBtn.style.background = '#a855f7';
            saveBtn.onclick = function() {
                saveCloudConfig();
            };
        }
        
        // Refresh connections
        fetchCloudConnections();
        if (typeof fetchPrimaryAIProvider === 'function') {
            fetchPrimaryAIProvider();
        }
    } catch (e) {
        console.error('Error updating cloud connection:', e);
        showToast('Error updating configuration: ' + e.message, 'error');
    }
}

// ============ DELETE CLOUD CONNECTION ============
async function deleteCloudConnection(name) {
    if (!confirm(`Delete connection "${name}"? This cannot be undone.`)) return;
    
    try {
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider/${name}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete');
        const data = await res.json();
        
        showToast(`✅ ${name} deleted`, 'info');
        fetchCloudConnections();
        if (typeof fetchPrimaryAIProvider === 'function') {
            fetchPrimaryAIProvider();
        }
    } catch (e) {
        console.error('Error deleting cloud connection:', e);
        showToast('Error deleting configuration: ' + e.message, 'error');
    }
}

console.log('✅ reload.js loaded - All cloud connection functions available');

// ============ PROVIDER MANAGEMENT FUNCTIONS ============
// These are defined globally so they work across all tabs

window.showAddProvider = function() {
    const modal = document.getElementById('add-provider-modal');
    if (modal) {
        modal.style.display = 'block';
    } else {
        console.warn('add-provider-modal not found - creating one');
        // Create modal dynamically if it doesn't exist
        const newModal = document.createElement('div');
        newModal.id = 'add-provider-modal';
        newModal.style.cssText = 'display:block; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); z-index:1000; padding:40px; box-sizing:border-box;';
        newModal.innerHTML = `
            <div style="max-width:500px; margin:100px auto; background:#0f172a; padding:30px; border-radius:12px; border:1px solid #1e293b;">
                <h3 style="color:#f1f5f9; margin-top:0;">➕ Add Cloud Provider</h3>
                <div class="form-group" style="margin-bottom:12px;">
                    <label style="color:#94a3b8; font-size:13px; display:block; margin-bottom:4px;">Provider Name</label>
                    <input type="text" id="cloud-api-name" placeholder="e.g., openai, anthropic" style="width:100%; padding:8px 12px; background:#1e293b; border:1px solid #334155; border-radius:6px; color:#f1f5f9;">
                </div>
                <div class="form-group" style="margin-bottom:12px;">
                    <label style="color:#94a3b8; font-size:13px; display:block; margin-bottom:4px;">Host URL</label>
                    <input type="text" id="cloud-api-host" placeholder="https://api.example.com/v1" style="width:100%; padding:8px 12px; background:#1e293b; border:1px solid #334155; border-radius:6px; color:#f1f5f9;">
                </div>
                <div class="form-group" style="margin-bottom:12px;">
                    <label style="color:#94a3b8; font-size:13px; display:block; margin-bottom:4px;">API Key</label>
                    <input type="password" id="cloud-api-key" placeholder="sk-..." style="width:100%; padding:8px 12px; background:#1e293b; border:1px solid #334155; border-radius:6px; color:#f1f5f9;">
                </div>
                <div class="form-group" style="margin-bottom:12px;">
                    <label style="color:#94a3b8; font-size:13px; display:block; margin-bottom:4px;">Default Model</label>
                    <input type="text" id="cloud-api-model" placeholder="gpt-4, claude-3, etc." style="width:100%; padding:8px 12px; background:#1e293b; border:1px solid #334155; border-radius:6px; color:#f1f5f9;">
                </div>
                <div style="display:flex; gap:10px; margin-top:20px;">
                    <button class="btn" style="background:#34d399; color:#0f172a; flex:1;" onclick="saveCloudConfig()">💾 Save</button>
                    <button class="btn" style="background:#1e293b; flex:1;" onclick="closeAddProvider()">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(newModal);
    }
};

window.closeAddProvider = function() {
    const modal = document.getElementById('add-provider-modal');
    if (modal) modal.style.display = 'none';
    document.getElementById('cloud-api-name').value = '';
    document.getElementById('cloud-api-host').value = '';
    document.getElementById('cloud-api-key').value = '';
    document.getElementById('cloud-api-model').value = '';
};

window.reloadApiKeys = function() {
    showToast('🔄 Reloading API keys from .env...', 'info');
    fetch('/api/v1/admin/dashboard/config/reload-api-keys', {method: 'POST'})
        .then(r => r.json())
        .then(data => {
            showToast(data.message || '✅ API keys reloaded', 'success');
            setTimeout(fetchCloudConnections, 500);
        })
        .catch(e => showToast('Error reloading API keys: ' + e.message, 'error'));
};

window.refreshBOM = function() {
    showToast('📋 Refreshing Bill of Materials...', 'info');
    if (typeof fetchCloudConnections === 'function') {
        fetchCloudConnections();
    }
    if (typeof fetchInstalledModels === 'function') {
        fetchInstalledModels();
    }
};

window.saveCloudConfig = async function() {
    const provider = document.getElementById('cloud-api-name').value;
    const host = document.getElementById('cloud-api-host').value;
    const api_key = document.getElementById('cloud-api-key').value;
    const model = document.getElementById('cloud-api-model').value;
    
    if (!provider) {
        showToast('Connection name is required', 'error');
        return;
    }
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, host, api_key, model })
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        showToast(`Configuration for ${provider} saved`, 'success');
        closeAddProvider();
        if (typeof fetchCloudConnections === 'function') {
            fetchCloudConnections();
        }
    } catch (e) {
        showToast('Failed to save: ' + e.message, 'error');
    }
};

console.log('✅ Provider management functions loaded globally');
