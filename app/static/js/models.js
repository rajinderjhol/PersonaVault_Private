// ============================================================
// MODEL MANAGEMENT - Complete Unified JavaScript
// ============================================================

console.log('📦 Model Management JS loading...');

// ============ PROVIDER MANAGEMENT ============

// Get all providers from the system
async function getAllProviders() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-providers/cloud');
        if (!res.ok) throw new Error('Failed to fetch providers');
        return await res.json();
    } catch (e) {
        console.error('Error fetching providers:', e);
        return [];
    }
}

// Render providers table
async function renderProvidersTable() {
    const tbody = document.getElementById('providers-table-body');
    if (!tbody) return;
    
    try {
        const providers = await getAllProviders();
        
        if (!providers || providers.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="padding:20px; text-align:center; color:#64748b;">
                        No providers configured. Add one using the form above or reload from .env.
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = providers.map(p => {
            const isActive = p.enabled === 'true' || p.enabled === true;
            const type = p.name === 'ollama' ? '🔒 Local' : '☁️ Cloud';
            const statusColor = isActive ? '#34d399' : '#64748b';
            const statusText = isActive ? '✅ Active' : '⏸️ Disabled';
            
            return `
                <tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:8px 6px;">
                        <span style="font-weight:600; color:#f1f5f9;">${p.name}</span>
                        ${p.primary ? ' <span style="font-size:9px; color:#fbbf24;">⭐ Primary</span>' : ''}
                    </td>
                    <td style="padding:8px 6px; color:#94a3b8;">${type}</td>
                    <td style="padding:8px 6px; color:#94a3b8;">${p.model || 'Default'}</td>
                    <td style="padding:8px 6px;">
                        <span style="color:${statusColor}; font-size:12px;">${statusText}</span>
                        ${p.host ? `<div style="font-size:9px; color:#64748b;">${p.host}</div>` : ''}
                    </td>
                    <td style="padding:8px 6px;">
                        <div style="display:flex; gap:4px; flex-wrap:wrap;">
                            <button class="refresh-btn" style="color:#38bdf8; border-color:#38bdf8; padding:2px 8px; font-size:9px;" onclick="editProvider('${p.name}')">
                                ✏️
                            </button>
                            <button class="refresh-btn" style="color:#34d399; border-color:#34d399; padding:2px 8px; font-size:9px;" onclick="viewProviderDetails('${p.name}')">
                                📋
                            </button>
                            ${p.name !== 'ollama' ? `
                                <button class="refresh-btn" style="color:#f87171; border-color:#f87171; padding:2px 8px; font-size:9px;" onclick="deleteProvider('${p.name}')">
                                    🗑️
                                </button>
                            ` : `
                                <span style="font-size:9px; color:#64748b; padding:2px 4px;">🛡️ Protected</span>
                            `}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (e) {
        console.error('Error rendering providers:', e);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="padding:20px; text-align:center; color:#f87171;">
                    Error loading providers
                </td>
            </tr>
        `;
    }
}

// Edit provider - fill form with existing data
window.editProvider = async function(name) {
    try {
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider-settings/${name}`);
        if (!res.ok) throw new Error('Failed to fetch config');
        const data = await res.json();
        
        document.getElementById('provider-name').value = name;
        document.getElementById('provider-host').value = data.host || '';
        document.getElementById('provider-api-key').value = data.api_key || '';
        document.getElementById('provider-model').value = data.model || '';
        
        // Change button to update
        const saveBtn = document.querySelector('#provider-form .btn:nth-child(2)');
        if (saveBtn) {
            saveBtn.textContent = 'Update Provider';
            saveBtn.style.background = '#fbbf24';
            saveBtn.onclick = function() { updateProvider(name); };
        }
        
        showToast(`Editing ${name} configuration`, 'info');
    } catch (e) {
        console.error('Error editing provider:', e);
        showToast('Error loading configuration', 'error');
    }
};

// Update provider
window.updateProvider = async function(name) {
    const host = document.getElementById('provider-host').value.trim();
    const apiKey = document.getElementById('provider-api-key').value.trim();
    const model = document.getElementById('provider-model').value.trim();
    
    if (!host || !model) {
        showToast('Please fill in Host and Model', 'error');
        return;
    }
    
    try {
        const body = { provider: name, host, model };
        if (apiKey) body.api_key = apiKey;
        
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!res.ok) throw new Error('Failed to update');
        
        showToast(`✅ ${name} configuration updated`, 'success');
        clearProviderForm();
        renderProvidersTable();
        refreshAllProviderStats();
    } catch (e) {
        console.error('Error updating provider:', e);
        showToast('Error updating configuration', 'error');
    }
};

// Delete provider
window.deleteProvider = async function(name) {
    if (!confirm(`Delete provider "${name}"? This cannot be undone.`)) return;
    
    try {
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider/${name}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete');
        
        showToast(`✅ ${name} deleted`, 'info');
        renderProvidersTable();
        refreshAllProviderStats();
        fetchPrimaryAIProvider();
    } catch (e) {
        console.error('Error deleting provider:', e);
        showToast('Error deleting configuration', 'error');
    }
};

// View provider details
window.viewProviderDetails = async function(name) {
    try {
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider-settings/${name}`);
        if (!res.ok) throw new Error('Failed to fetch config');
        const data = await res.json();
        
        const details = `
            <div style="background:#020617; padding:16px; border-radius:8px; border:1px solid #334155;">
                <h4 style="color:#f472b6; margin:0 0 10px 0;">🔌 ${name} Details</h4>
                <div style="font-size:12px; color:#94a3b8;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                        <div><span style="color:#64748b;">Name:</span> ${name}</div>
                        <div><span style="color:#64748b;">Type:</span> ${name === 'ollama' ? 'Local' : 'Cloud'}</div>
                        <div><span style="color:#64748b;">Host:</span> ${data.host || 'Default'}</div>
                        <div><span style="color:#64748b;">Model:</span> ${data.model || 'Default'}</div>
                        <div><span style="color:#64748b;">API Key:</span> ${data.api_key ? '••••••••' : 'Not set'}</div>
                        <div><span style="color:#64748b;">Status:</span> ${data.enabled ? '✅ Active' : '❌ Disabled'}</div>
                    </div>
                </div>
            </div>
        `;
        
        showModal('Provider Details', details, [
            { text: '✏️ Edit', class: 'btn', style: 'background:#38bdf8;color:#0f172a;', onclick: `editProvider('${name}')` },
            { text: 'Close', class: 'btn', style: 'background:#334155;', onclick: 'closeModal()' }
        ]);
        
    } catch (e) {
        console.error('Error viewing provider details:', e);
        showToast('Error loading details', 'error');
    }
};

// Save new provider
window.saveProviderConfig = async function() {
    const name = document.getElementById('provider-name').value.trim();
    const host = document.getElementById('provider-host').value.trim();
    const apiKey = document.getElementById('provider-api-key').value.trim();
    const model = document.getElementById('provider-model').value.trim();
    
    if (!name || !host || !model) {
        showToast('Please fill in Name, Host, and Model', 'error');
        return;
    }
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: name,
                host: host,
                api_key: apiKey || '',
                model: model
            })
        });
        
        if (!res.ok) throw new Error('Failed to save');
        
        showToast(`✅ ${name} configured successfully`, 'success');
        clearProviderForm();
        renderProvidersTable();
        refreshAllProviderStats();
        fetchPrimaryAIProvider();
    } catch (e) {
        console.error('Error saving provider:', e);
        showToast('Error saving configuration', 'error');
    }
};

// Test provider connection
window.testProviderConnection = async function() {
    const name = document.getElementById('provider-name').value.trim();
    const host = document.getElementById('provider-host').value.trim();
    const apiKey = document.getElementById('provider-api-key').value.trim();
    const model = document.getElementById('provider-model').value.trim();
    
    if (!name || !host) {
        showToast('Please fill in Name and Host', 'error');
        return;
    }
    
    showToast('Testing connection...', 'info');
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-test', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: name,
                host: host,
                api_key: apiKey,
                model: model || 'default'
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showToast('✅ Connection successful!', 'success');
        } else {
            showToast('❌ Connection failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (e) {
        console.error('Error testing connection:', e);
        showToast('Error testing connection', 'error');
    }
};

// Clear provider form
window.clearProviderForm = function() {
    document.getElementById('provider-name').value = '';
    document.getElementById('provider-host').value = '';
    document.getElementById('provider-api-key').value = '';
    document.getElementById('provider-model').value = '';
    
    // Reset button
    const saveBtn = document.querySelector('#provider-form .btn:nth-child(2)');
    if (saveBtn) {
        saveBtn.textContent = 'Save';
        saveBtn.style.background = '#a855f7';
        saveBtn.onclick = window.saveProviderConfig;
    }
    
    showToast('Form cleared', 'info');
};

// ============ PRIMARY AI PROVIDER ============
async function fetchPrimaryAIProvider() {
    const select = document.getElementById('primary-ai-provider-select');
    const status = document.getElementById('primary-ai-provider-status');
    
    if (!select) return;
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error('Failed to fetch provider');
        const data = await res.json();
        
        const provider = data.primary_provider || 'ollama';
        select.value = provider;
        
        if (status) {
            status.textContent = `✅ Active: ${provider}`;
            status.className = 'tag tag-success';
        }
    } catch (e) {
        console.error('Error fetching primary provider:', e);
        if (status) {
            status.textContent = '❌ Error loading';
            status.className = 'tag tag-error';
        }
    }
}

window.updatePrimaryAIProvider = async function(value) {
    const status = document.getElementById('primary-ai-provider-status');
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider: value })
        });
        
        if (!res.ok) throw new Error('Failed to update provider');
        
        if (status) {
            status.textContent = `✅ Updated: ${value}`;
            status.className = 'tag tag-success';
        }
        
        showToast(`✅ Primary provider set to ${value}`, 'success');
        
        const contextEl = document.getElementById('context-provider');
        if (contextEl) contextEl.textContent = value;
        
        const chatSelect = document.getElementById('chat-provider');
        if (chatSelect) chatSelect.value = value;
    } catch (e) {
        console.error('Error updating provider:', e);
        if (status) {
            status.textContent = '❌ Update failed';
            status.className = 'tag tag-error';
        }
        showToast('Error updating provider', 'error');
    }
};

// ============ PROVIDER STATS ============
window.refreshAllProviderStats = async function() {
    const container = document.getElementById('provider-stats-container');
    if (!container) return;
    
    container.innerHTML = '<div class="metric-label">Loading stats...</div>';
    
    const providers = ['groq', 'ollama', 'gemini', 'deepseek'];
    let html = '<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px;">';
    
    for (const provider of providers) {
        try {
            const res = await fetch(`/api/v1/admin/dashboard/models/provider-stats/${provider}`);
            if (res.ok) {
                const data = await res.json();
                const statusColor = data.status === 'OK' || data.status === 'Local - Unlimited' ? '#34d399' : '#f87171';
                html += `
                    <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px 14px;">
                        <div style="font-weight:600; color:${statusColor}; font-size:13px; text-transform:capitalize;">${provider}</div>
                        <div style="font-size:11px; color:#94a3b8; margin-top:4px;">
                            <div>Requests: ${data.remaining_requests !== undefined ? data.remaining_requests : 'N/A'}</div>
                            <div>Tokens: ${data.remaining_tokens !== undefined ? data.remaining_tokens : 'N/A'}</div>
                            <div style="font-size:10px; color:#64748b;">Status: ${data.status || 'Unknown'}</div>
                            ${data.reset_requests ? `<div style="font-size:9px; color:#64748b; margin-top:2px;">Reset: ${new Date(data.reset_requests).toLocaleString()}</div>` : ''}
                            ${data.cost_per_token ? `<div style="font-size:9px; color:#64748b; margin-top:2px;">💰 $${data.cost_per_token}/1K tokens</div>` : ''}
                        </div>
                    </div>
                `;
            } else {
                html += `
                    <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px 14px;">
                        <div style="font-weight:600; color:#64748b; font-size:13px; text-transform:capitalize;">${provider}</div>
                        <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Not configured</div>
                    </div>
                `;
            }
        } catch (e) {
            html += `
                <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px 14px;">
                    <div style="font-weight:600; color:#f87171; font-size:13px; text-transform:capitalize;">${provider}</div>
                    <div style="font-size:11px; color:#94a3b8; margin-top:4px;">Error loading</div>
                </div>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
};

// ============ AI BILL OF MATERIALS ============
window.refreshAIBOM = async function() {
    const container = document.getElementById('ai-bom-container');
    if (!container) return;
    
    container.innerHTML = '<div class="metric-label">Loading BOM...</div>';
    
    try {
        // Get providers
        const providers = await getAllProviders();
        
        // Get installed models
        const modelsRes = await fetch('/api/v1/admin/dashboard/models');
        const modelsData = await modelsRes.json();
        const installedModels = modelsData.models || [];
        
        // Build BOM
        let html = `
            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; margin-bottom:12px;">
                <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px;">
                    <div style="font-size:11px; color:#64748b;">Total Providers</div>
                    <div style="font-size:24px; font-weight:600; color:#f1f5f9;">${providers.length}</div>
                </div>
                <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px;">
                    <div style="font-size:11px; color:#64748b;">Installed Models</div>
                    <div style="font-size:24px; font-weight:600; color:#f1f5f9;">${installedModels.length}</div>
                </div>
                <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:10px;">
                    <div style="font-size:11px; color:#64748b;">Active Provider</div>
                    <div style="font-size:24px; font-weight:600; color:#34d399;">${document.getElementById('primary-ai-provider-select')?.value || 'ollama'}</div>
                </div>
            </div>
            <div style="background:#020617; border:1px solid #334155; border-radius:6px; padding:12px; font-size:12px; color:#94a3b8;">
                <div style="font-weight:600; color:#fbbf24; margin-bottom:8px;">📋 Component Inventory</div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:4px;">
                    ${providers.map(p => `
                        <div style="display:flex; justify-content:space-between; padding:2px 4px; border-bottom:1px solid #1e293b;">
                            <span>${p.name}</span>
                            <span style="color:#64748b;">${p.model || 'Default'}</span>
                        </div>
                    `).join('')}
                    ${installedModels.map(m => `
                        <div style="display:flex; justify-content:space-between; padding:2px 4px; border-bottom:1px solid #1e293b;">
                            <span>📦 ${m.name}</span>
                            <span style="color:#64748b;">${m.size ? (m.size / 1024 / 1024 / 1024).toFixed(2) + ' GB' : 'Unknown'}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        
    } catch (e) {
        console.error('Error loading BOM:', e);
        container.innerHTML = '<div style="color:#f87171;">Error loading AI BOM</div>';
    }
};

// ============ INSTALLED MODELS ============
window.fetchModels = async function() {
    const list = document.getElementById('models-list');
    if (!list) return;
    
    list.innerHTML = '<div class="metric-label">Loading models...</div>';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        const data = await res.json();
        
        const models = data.models || [];
        const activeModel = data.active_model || 'tinydolphin';
        
        // Update count
        const countEl = document.getElementById('model-count');
        if (countEl) countEl.textContent = `${models.length} model(s) installed`;
        
        if (models.length === 0) {
            list.innerHTML = '<div class="metric-label">No models installed. Pull one using the form above.</div>';
            return;
        }
        
        // Sort: active model first
        models.sort((a, b) => {
            const aName = a.name || '';
            const bName = b.name || '';
            if (aName === activeModel) return -1;
            if (bName === activeModel) return 1;
            return aName.localeCompare(bName);
        });
        
        const protectedModels = ['tinydolphin:latest', 'tinydolphin'];
        
        list.innerHTML = models.map(m => {
            const name = m.name || 'Unknown';
            const isActive = name === activeModel;
            const isProtected = protectedModels.some(p => name.includes(p));
            const size = m.size ? `${(m.size / 1024 / 1024 / 1024).toFixed(2)} GB` : 'Unknown';
            const modified = m.modified_at ? new Date(m.modified_at).toLocaleString() : 'Unknown';
            
            return `
                <div style="display:flex; justify-content:space-between; padding:10px 12px; background:${isActive ? '#1a2a3a' : '#020617'}; border-radius:6px; border:1px solid ${isActive ? '#34d399' : '#334155'}; align-items:center;">
                    <div style="flex:1;">
                        <div style="font-weight:600; color:${isActive ? '#34d399' : '#f1f5f9'};">
                            ${isActive ? '🟢 ' : '📦 '}${name}
                            ${isActive ? '<span style="font-size:10px; color:#34d399; margin-left:8px;">(Active)</span>' : ''}
                            ${isProtected ? '<span style="font-size:10px; color:#fbbf24; margin-left:8px;">🛡️ Protected</span>' : ''}
                        </div>
                        <div style="font-size:11px; color:#64748b; margin-top:2px;">
                            Size: ${size} | Modified: ${modified}
                        </div>
                        <div style="font-size:10px; color:#64748b; margin-top:1px;">
                            Path: ${m.path || '/usr/local/ollama/models'}
                        </div>
                    </div>
                    <div style="display:flex; gap:4px; flex-wrap:wrap;">
                        ${!isActive ? `
                            <button class="refresh-btn" style="color:#34d399; border-color:#34d399; padding:2px 8px; font-size:9px;" onclick="setActiveModel('${name}')">
                                ⭐ Active
                            </button>
                        ` : `
                            <button class="refresh-btn" style="color:#94a3b8; border-color:#94a3b8; padding:2px 8px; font-size:9px;" onclick="viewModelDetails('${name}')">
                                📋 Details
                            </button>
                        `}
                        ${!isProtected ? `
                            <button class="refresh-btn" style="color:#f87171; border-color:#f87171; padding:2px 8px; font-size:9px;" onclick="deleteModel('${name}')">
                                🗑️ Delete
                            </button>
                        ` : `
                            <span style="font-size:9px; color:#64748b; padding:2px 4px;">🛡️ Protected</span>
                        `}
                    </div>
                </div>
            `;
        }).join('');
    } catch (e) {
        console.error('Error fetching models:', e);
        list.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading models</div>';
    }
};

// ============ MODAL FUNCTIONS ============
function showModal(title, content, buttons = []) {
    const existing = document.getElementById('custom-modal');
    if (existing) existing.remove();
    
    const modal = document.createElement('div');
    modal.id = 'custom-modal';
    modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.8);z-index:9999;display:flex;align-items:center;justify-content:center;';
    
    let buttonsHtml = buttons.map(b => `
        <button class="${b.class}" style="${b.style || ''}" onclick="${b.onclick}">${b.text}</button>
    `).join('');
    
    modal.innerHTML = `
        <div style="background:#1e293b;padding:24px;border-radius:12px;max-width:500px;width:90%;border:1px solid #334155;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2 style="color:#f472b6;margin:0;">${title}</h2>
                <button onclick="closeModal()" style="background:none;border:none;color:#94a3b8;font-size:20px;cursor:pointer;">✕</button>
            </div>
            ${content}
            <div style="margin-top:16px;display:flex;gap:8px;flex-wrap:wrap;">
                ${buttonsHtml}
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function closeModal() {
    const modal = document.getElementById('custom-modal');
    if (modal) modal.remove();
}

// ============ SHARED FUNCTIONS ============
window.setActiveModel = async function(modelName) {
    try {
        const res = await fetch('/api/v1/admin/dashboard/models/set-active', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: modelName })
        });
        
        if (!res.ok) throw new Error('Failed to set active model');
        
        showToast(`✅ ${modelName} set as active model`, 'success');
        fetchModels();
        refreshAIBOM();
    } catch (e) {
        console.error('Error setting active model:', e);
        showToast('Error setting active model', 'error');
    }
};

window.deleteModel = async function(modelName) {
    if (!confirm(`Delete model "${modelName}"? This cannot be undone.`)) return;
    
    try {
        const res = await fetch(`/api/v1/admin/dashboard/models/${modelName}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Failed to delete model');
        
        showToast(`✅ ${modelName} deleted`, 'info');
        fetchModels();
        refreshAIBOM();
    } catch (e) {
        console.error('Error deleting model:', e);
        showToast('Error deleting model', 'error');
    }
};

window.viewModelDetails = async function(modelName) {
    try {
        const res = await fetch('/api/v1/admin/dashboard/models');
        if (!res.ok) throw new Error('Failed to fetch models');
        const data = await res.json();
        const model = data.models.find(m => m.name === modelName);
        
        if (!model) {
            showToast('Model details not found', 'error');
            return;
        }
        
        const details = `
            <div style="background:#020617; padding:16px; border-radius:8px; border:1px solid #334155;">
                <h4 style="color:#34d399; margin:0 0 10px 0;">📦 ${model.name}</h4>
                <div style="font-size:12px; color:#94a3b8;">
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                        <div><span style="color:#64748b;">Name:</span> ${model.name}</div>
                        <div><span style="color:#64748b;">Size:</span> ${model.size ? (model.size / 1024 / 1024 / 1024).toFixed(2) : 'Unknown'} GB</div>
                        <div><span style="color:#64748b;">Modified:</span> ${model.modified_at ? new Date(model.modified_at).toLocaleString() : 'Unknown'}</div>
                        <div><span style="color:#64748b;">Digest:</span> ${model.digest ? model.digest.substring(0, 12) + '...' : 'Unknown'}</div>
                        ${model.details ? `
                            <div><span style="color:#64748b;">Family:</span> ${model.details.family || 'Unknown'}</div>
                            <div><span style="color:#64748b;">Parameter Size:</span> ${model.details.parameter_size || 'Unknown'}</div>
                            <div><span style="color:#64748b;">Quantization:</span> ${model.details.quantization_level || 'Unknown'}</div>
                            <div><span style="color:#64748b;">Context Length:</span> ${model.details.context_length || 'Unknown'}</div>
                        ` : ''}
                        <div style="grid-column: span 2;">
                            <span style="color:#64748b;">Path:</span> ${model.path || '/usr/local/ollama/models'}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        showModal('Model Details', details, [
            { text: 'Close', class: 'btn', style: 'background:#334155;', onclick: 'closeModal()' }
        ]);
        
    } catch (e) {
        console.error('Error viewing model details:', e);
        showToast('Error loading model details', 'error');
    }
};

// ============ PULL MODEL ============
window.triggerModelPull = async function() {
    const input = document.getElementById('new-model-input');
    const modelName = input.value.trim();
    
    if (!modelName) {
        showToast('Please enter a model name', 'error');
        return;
    }
    
    const progressContainer = document.getElementById('pull-progress-container');
    const progressBar = document.getElementById('pull-progress-bar');
    const progressLabel = document.getElementById('pull-status-label');
    const percentageLabel = document.getElementById('pull-percentage');
    const statusDiv = document.getElementById('pull-status');
    
    progressContainer.style.display = 'block';
    statusDiv.style.display = 'block';
    progressBar.style.width = '0%';
    percentageLabel.textContent = '0%';
    progressLabel.textContent = `Pulling ${modelName}...`;
    statusDiv.textContent = 'Starting pull...';
    
    try {
        const response = await fetch('/api/v1/admin/dashboard/models/pull', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: modelName })
        });
        
        if (!response.ok) throw new Error('Failed to pull model');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(l => l.trim());
            
            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    
                    if (data.error) {
                        statusDiv.textContent = `❌ Error: ${data.error}`;
                        progressLabel.textContent = 'Failed';
                        percentageLabel.textContent = '❌';
                        showToast('Error pulling model', 'error');
                        return;
                    }
                    
                    if (data.status) {
                        statusDiv.textContent = data.status;
                        progressLabel.textContent = data.status;
                    }
                    
                    if (data.completed !== undefined && data.total !== undefined) {
                        const percent = Math.round((data.completed / data.total) * 100);
                        progressBar.style.width = `${percent}%`;
                        percentageLabel.textContent = `${percent}%`;
                    }
                    
                    if (data.digest) {
                        statusDiv.textContent = `Downloading: ${data.digest.substring(0, 12)}...`;
                    }
                    
                } catch (e) {
                    statusDiv.textContent += '\n' + line;
                }
            }
        }
        
        progressLabel.textContent = '✅ Complete!';
        percentageLabel.textContent = '✅';
        progressBar.style.width = '100%';
        showToast(`✅ ${modelName} pulled successfully`, 'success');
        input.value = '';
        fetchModels();
        refreshAIBOM();
        
    } catch (e) {
        console.error('Error pulling model:', e);
        progressLabel.textContent = '❌ Failed';
        percentageLabel.textContent = '❌';
        showToast('Error pulling model', 'error');
    }
};

// ============ RELOAD API KEYS ============
window.reloadApiKeys = async function() {
    const statusEl = document.getElementById('reload-status');
    const resultEl = document.getElementById('reload-result');
    
    statusEl.textContent = '⏳ Reloading API keys from .env...';
    statusEl.style.color = '#fbbf24';
    resultEl.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/reload-api-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            statusEl.textContent = '✅ ' + data.message;
            statusEl.style.color = '#34d399';
            
            resultEl.style.display = 'block';
            resultEl.innerHTML = `
                <div style="color: #34d399;">✅ Successfully loaded ${data.providers_loaded?.length || 0} provider(s)</div>
                <div style="color: #94a3b8; margin-top: 4px;">Providers: ${data.providers_loaded?.join(', ') || 'None'}</div>
                <div style="color: #64748b; margin-top: 4px; font-size: 11px;">Env vars found: ${data.env_vars_found?.join(', ') || 'None'}</div>
            `;
            
            renderProvidersTable();
            refreshAllProviderStats();
            fetchPrimaryAIProvider();
            refreshAIBOM();
        } else if (data.status === 'no_keys_found') {
            statusEl.textContent = '⚠️ ' + data.message;
            statusEl.style.color = '#fbbf24';
            resultEl.style.display = 'block';
            resultEl.innerHTML = `
                <div style="color: #fbbf24;">⚠️ ${data.message}</div>
                <div style="color: #64748b; margin-top: 4px; font-size: 11px;">Env vars found: ${data.env_vars_found?.join(', ') || 'None'}</div>
            `;
        } else {
            statusEl.textContent = '❌ Error: ' + (data.error || 'Unknown error');
            statusEl.style.color = '#f87171';
        }
    } catch (e) {
        statusEl.textContent = '❌ Network error: ' + e.message;
        statusEl.style.color = '#f87171';
        console.error('Reload error:', e);
    }
};

// ============ TOAST ============
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.style.cssText = `
        padding: 8px 14px;
        border-radius: 6px;
        background: ${type === 'error' ? '#7f1d1d' : type === 'success' ? '#14532d' : '#1e293b'};
        color: #f1f5f9;
        border: 1px solid ${type === 'error' ? '#f87171' : type === 'success' ? '#34d399' : '#334155'};
        font-size: 12px;
        animation: slideIn 0.3s ease;
        max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    `;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============ INITIALIZATION ============
function initModelsTab() {
    console.log('📦 Initializing models tab...');
    fetchPrimaryAIProvider();
    renderProvidersTable();
    fetchModels();
    refreshAllProviderStats();
    refreshAIBOM();
}

// Check if models tab is already loaded
if (document.getElementById('models-tab')) {
    console.log('📦 Models tab already present, initializing...');
    setTimeout(initModelsTab, 500);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('📦 DOM loaded, checking for models tab...');
    setTimeout(function() {
        if (document.getElementById('models-tab')) {
            console.log('📦 Models tab found after DOM load, initializing...');
            initModelsTab();
        }
    }, 1000);
});

// Hook into dashboard tab switching
if (window.switchTab) {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tabId) {
        originalSwitchTab(tabId);
        if (tabId === 'models') {
            console.log('📦 Switched to models tab, initializing...');
            setTimeout(initModelsTab, 500);
        }
    };
}

console.log('✅ Model Management JS loaded');

// ============ RENDER PROVIDERS TABLE WITH EDIT ACTIONS ============
async function renderProvidersTable() {
    const tbody = document.getElementById('providers-table-body');
    if (!tbody) return;
    
    try {
        const providers = await getAllProviders();
        
        if (!providers || providers.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" style="padding:20px; text-align:center; color:#64748b;">
                        No providers configured. Click "Add New Provider" below.
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = providers.map(p => {
            const isActive = p.enabled === 'true' || p.enabled === true;
            const type = p.name === 'ollama' ? '🔒 Local' : '☁️ Cloud';
            const statusColor = isActive ? '#34d399' : '#64748b';
            const statusText = isActive ? '✅ Active' : '⏸️ Disabled';
            
            return `
                <tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:10px 8px;">
                        <span style="font-weight:600; color:#f1f5f9;">${p.name}</span>
                        ${p.primary ? ' <span style="font-size:9px; color:#fbbf24;">⭐ Primary</span>' : ''}
                        <div style="font-size:9px; color:#64748b; margin-top:2px;">${type}</div>
                    </td>
                    <td style="padding:10px 8px; color:#94a3b8;">
                        ${p.model || 'Default'}
                        <div style="font-size:9px; color:#64748b; margin-top:2px;">${p.host || 'Local'}</div>
                    </td>
                    <td style="padding:10px 8px; color:#94a3b8; font-size:11px;">${p.host || 'N/A'}</td>
                    <td style="padding:10px 8px;">
                        <span style="color:${statusColor}; font-size:12px;">${statusText}</span>
                        ${p.api_key ? `<div style="font-size:9px; color:#64748b;">🔑 ${p.api_key.substring(0, 4)}...${p.api_key.substring(p.api_key.length - 4)}</div>` : ''}
                    </td>
                    <td style="padding:10px 8px;">
                        <div style="display:flex; gap:4px; flex-wrap:wrap;">
                            <button class="refresh-btn" style="color:#38bdf8; border-color:#38bdf8; padding:4px 10px; font-size:10px;" onclick="editProvider('${p.name}')">
                                ✏️ Edit
                            </button>
                            <button class="refresh-btn" style="color:#94a3b8; border-color:#94a3b8; padding:4px 10px; font-size:10px;" onclick="viewProviderDetails('${p.name}')">
                                📋 Details
                            </button>
                            ${p.name !== 'ollama' ? `
                                <button class="refresh-btn" style="color:#f87171; border-color:#f87171; padding:4px 10px; font-size:10px;" onclick="deleteProvider('${p.name}')">
                                    🗑️ Delete
                                </button>
                            ` : `
                                <span style="font-size:9px; color:#64748b; padding:4px 8px;">🛡️ Protected</span>
                            `}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (e) {
        console.error('Error rendering providers:', e);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="padding:20px; text-align:center; color:#f87171;">
                    Error loading providers
                </td>
            </tr>
        `;
    }
}

// ============ EDIT PROVIDER - CLEAR ACTION ============
window.editProvider = async function(name) {
    try {
        // Show the form container
        const container = document.getElementById('provider-form-container');
        container.style.display = 'block';
        
        // Update title
        document.getElementById('provider-form-title').textContent = `✏️ Editing: ${name}`;
        document.getElementById('provider-form-title').style.color = '#38bdf8';
        
        // Fetch current config
        const res = await fetch(`/api/v1/admin/dashboard/config/ai-provider-settings/${name}`);
        if (!res.ok) throw new Error('Failed to fetch config');
        const data = await res.json();
        
        // Fill form
        document.getElementById('provider-name').value = name;
        document.getElementById('provider-host').value = data.host || '';
        document.getElementById('provider-api-key').value = data.api_key || '';
        document.getElementById('provider-model').value = data.model || '';
        
        // Update button to save
        const saveBtn = document.querySelector('#provider-form-container .btn:first-child');
        if (saveBtn) {
            saveBtn.textContent = '💾 Save Changes';
            saveBtn.style.background = '#34d399';
            saveBtn.style.color = '#0f172a';
            saveBtn.onclick = function() { saveProviderConfig(); };
        }
        
        // Scroll to form
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        showToast(`✏️ Editing ${name} - update the fields below`, 'info');
        
    } catch (e) {
        console.error('Error editing provider:', e);
        showToast('Error loading configuration', 'error');
    }
};

// ============ SAVE PROVIDER CONFIG ============
window.saveProviderConfig = async function() {
    const name = document.getElementById('provider-name').value.trim();
    const host = document.getElementById('provider-host').value.trim();
    const apiKey = document.getElementById('provider-api-key').value.trim();
    const model = document.getElementById('provider-model').value.trim();
    
    if (!name || !host || !model) {
        showToast('Please fill in Name, Host, and Model', 'error');
        return;
    }
    
    const statusEl = document.getElementById('edit-status');
    statusEl.textContent = '⏳ Saving configuration...';
    statusEl.style.color = '#fbbf24';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/ai-provider-settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                provider: name,
                host: host,
                api_key: apiKey || '',
                model: model
            })
        });
        
        if (!res.ok) throw new Error('Failed to save');
        
        statusEl.textContent = '✅ Configuration saved successfully!';
        statusEl.style.color = '#34d399';
        
        showToast(`✅ ${name} configured successfully`, 'success');
        
        // Reset form
        cancelProviderEdit();
        
        // Refresh tables
        renderProvidersTable();
        refreshAllProviderStats();
        fetchPrimaryAIProvider();
        refreshAIBOM();
        
    } catch (e) {
        console.error('Error saving provider:', e);
        statusEl.textContent = '❌ Error: ' + e.message;
        statusEl.style.color = '#f87171';
        showToast('Error saving configuration', 'error');
    }
};

// ============ CANCEL EDIT ============
window.cancelProviderEdit = function() {
    document.getElementById('provider-form-container').style.display = 'none';
    document.getElementById('provider-name').value = '';
    document.getElementById('provider-host').value = '';
    document.getElementById('provider-api-key').value = '';
    document.getElementById('provider-model').value = '';
    document.getElementById('edit-status').textContent = '';
    
    // Reset save button
    const saveBtn = document.querySelector('#provider-form-container .btn:first-child');
    if (saveBtn) {
        saveBtn.textContent = 'Save Changes';
        saveBtn.style.background = '#34d399';
        saveBtn.style.color = '#0f172a';
        saveBtn.onclick = function() { saveProviderConfig(); };
    }
};

// ============ SHOW ADD PROVIDER FORM ============
window.showAddProviderForm = function() {
    const container = document.getElementById('provider-form-container');
    container.style.display = 'block';
    
    document.getElementById('provider-form-title').textContent = '➕ Add New Provider';
    document.getElementById('provider-form-title').style.color = '#a855f7';
    
    document.getElementById('provider-name').value = '';
    document.getElementById('provider-name').readOnly = false;
    document.getElementById('provider-host').value = '';
    document.getElementById('provider-api-key').value = '';
    document.getElementById('provider-model').value = '';
    document.getElementById('edit-status').textContent = '';
    
    // Update save button
    const saveBtn = document.querySelector('#provider-form-container .btn:first-child');
    if (saveBtn) {
        saveBtn.textContent = '💾 Add Provider';
        saveBtn.style.background = '#a855f7';
        saveBtn.style.color = '#f1f5f9';
        saveBtn.onclick = function() { saveProviderConfig(); };
    }
    
    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
};

// ============ GET ALL PROVIDERS (Fixed) ============
async function getAllProviders() {
    try {
        // Get cloud providers
        const cloudRes = await fetch('/api/v1/admin/dashboard/config/ai-providers/cloud');
        let cloudProviders = [];
        if (cloudRes.ok) {
            cloudProviders = await cloudRes.json();
        }
        
        // Get primary provider
        const primaryRes = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        let primaryProvider = 'ollama';
        if (primaryRes.ok) {
            const data = await primaryRes.json();
            primaryProvider = data.primary_provider || 'ollama';
        }
        
        // Build provider list from all known providers
        const providerNames = ['ollama', 'groq', 'gemini', 'deepseek'];
        const allProviders = providerNames.map(name => {
            const cloud = cloudProviders.find(p => p.name === name);
            return {
                name: name,
                host: cloud?.host || (name === 'ollama' ? 'http://localhost:11434' : ''),
                model: cloud?.model || (name === 'ollama' ? 'tinydolphin:latest' : ''),
                enabled: cloud?.enabled !== undefined ? cloud.enabled : (name === 'ollama' || name === 'groq'),
                api_key: cloud?.api_key || '',
                primary: name === primaryProvider
            };
        });
        
        return allProviders;
    } catch (e) {
        console.error('Error fetching all providers:', e);
        // Return defaults
        return [
            { name: 'ollama', host: 'http://localhost:11434', model: 'tinydolphin:latest', enabled: true, primary: true },
            { name: 'groq', host: 'https://api.groq.com/openai/v1', model: 'qwen/qwen3.6-27b', enabled: true },
            { name: 'gemini', host: 'https://generativelanguage.googleapis.com/v1beta', model: 'gemini-2.0-flash-exp', enabled: false },
            { name: 'deepseek', host: 'https://api.deepseek.com/v1', model: 'deepseek-chat', enabled: false }
        ];
    }
}

// Also add a backend endpoint to get all provider settings
