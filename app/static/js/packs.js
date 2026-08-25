// Packs Management JavaScript
// Placeholder for behaviour pack functionality

async function fetchPacks() {
    const activeGrid = document.getElementById('active-packs-list');
    const inactiveGrid = document.getElementById('inactive-packs-list');
    
    if (!activeGrid || !inactiveGrid) return;
    
    activeGrid.innerHTML = '<div class="metric-label">Loading...</div>';
    inactiveGrid.innerHTML = '<div class="metric-label">Loading...</div>';
    
    try {
        const res = await fetch('/api/v1/packs/');
        const data = await res.json();
        const packs = data.packs || [];
        
        const activePacks = packs.filter(p => p.is_active);
        const inactivePacks = packs.filter(p => !p.is_active);
        
        const packHtml = (p) => `
            <div class="pack-card" style="background: #1e293b; padding: 10px; border-radius: 8px; margin-bottom: 5px; font-size: 12px;">
                <div style="display:flex; justify-content:space-between; align-items: center;">
                    <span style="font-weight:700; color:#38bdf8;">${p.name}</span>
                    <button class="btn" style="background: ${p.is_active ? '#fbbf24' : '#34d399'}; padding: 2px 5px; font-size: 10px;" onclick="togglePack('${p.id}')">
                        ${p.is_active ? 'Deactivate' : 'Activate'}
                    </button>
                </div>
            </div>
        `;
        
        activeGrid.innerHTML = activePacks.length > 0 ? activePacks.map(packHtml).join('') : '<div class="metric-label">No active packs</div>';
        inactiveGrid.innerHTML = inactivePacks.length > 0 ? inactivePacks.map(packHtml).join('') : '<div class="metric-label">No inactive packs</div>';
        
    } catch (e) {
        console.error('Pack fetch error:', e);
        activeGrid.innerHTML = '<div class="metric-label" style="color:#f87171;">Error</div>';
        inactiveGrid.innerHTML = '<div class="metric-label" style="color:#f87171;">Error</div>';
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
