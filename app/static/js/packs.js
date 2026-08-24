// Packs Management JavaScript
// Placeholder for behaviour pack functionality

async function fetchPacks() {
    const grid = document.getElementById('packs-grid');
    if (!grid) return;
    
    grid.innerHTML = '<div class="metric-label">Loading packs...</div>';
    try {
        const res = await fetch('/api/v1/packs/');
        const data = await res.json();
        const packs = data.packs || [];
        
        if (packs.length > 0) {
            grid.innerHTML = packs.map(p => `
                <div class="pack-card" style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid ${p.is_active ? '#34d399' : '#f87171'}; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items: center; margin-bottom: 10px;">
                        <span class="pack-name" style="font-weight:700; color:#38bdf8;">${p.name}</span>
                        <span class="tag ${p.is_active ? 'tag-success' : 'tag-danger'}">${p.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div class="pack-stats" style="color:#94a3b8; font-size: 12px; margin-bottom: 10px;">Domain: ${p.domain} | Version: ${p.version}</div>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn" style="background: ${p.is_active ? '#fbbf24' : '#34d399'}; padding: 5px 10px; font-size: 11px;" onclick="togglePack('${p.id}')">
                            ${p.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="btn" style="background: #f87171; padding: 5px 10px; font-size: 11px;" onclick="removePack('${p.id}')">
                            Remove
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            grid.innerHTML = '<div class="metric-label">No packs installed. Upload a pack to get started.</div>';
        }
    } catch (e) {
        console.error('Pack fetch error:', e);
        grid.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading packs</div>';
    }
}

async function togglePack(id) {
    try {
        const res = await fetch(`/api/v1/packs/${id}/toggle`, { method: 'POST' });
        if (res.ok) {
            showToast('Pack status updated', 'success');
            fetchPacks();
        } else {
            throw new Error('Failed to toggle pack');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function removePack(id) {
    if (!confirm('Are you sure you want to remove this pack?')) return;
    try {
        const res = await fetch(`/api/v1/packs/${id}`, { method: 'DELETE' });
        if (res.ok) {
            showToast('Pack removed', 'success');
            fetchPacks();
        } else {
            throw new Error('Failed to remove pack');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function installPack() {
    const fileInput = document.getElementById('pack-file-input');
    const status = document.getElementById('pack-install-status');
    const file = fileInput?.files?.[0];
    
    if (!file) {
        showToast('Select a YAML file', 'error');
        return;
    }
    
    status.textContent = 'Installing...';
    try {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/v1/packs/install', { method: 'POST', body: formData });
        const data = await res.json();
        if (res.ok) {
            status.textContent = '✅ ' + (data.message || 'Installed');
            showToast('Pack installed: ' + (data.name || ''), 'success');
            fetchPacks();
        } else {
            status.textContent = '❌ ' + (data.detail || 'Error');
            showToast('Install failed', 'error');
        }
    } catch (e) {
        status.textContent = '❌ ' + e.message;
        showToast('Install failed', 'error');
    }
}

async function bulkTogglePacks(activate) {
    try {
        const res = await fetch(`/api/v1/packs/bulk-toggle?activate=${activate}`, { method: 'POST' });
        if (res.ok) {
            showToast(`All packs ${activate ? 'activated' : 'deactivated'}`, 'success');
            fetchPacks();
        } else {
            throw new Error('Failed to bulk toggle packs');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

window.bulkTogglePacks = bulkTogglePacks;

console.log('✅ packs.js loaded');
