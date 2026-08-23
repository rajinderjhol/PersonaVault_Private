// ============ PACKS MANAGEMENT ============
async function fetchPacks() {
    // Use the correct IDs from packs.html
    const activeGrid = document.getElementById('active-packs-list');
    const inactiveGrid = document.getElementById('inactive-packs-list');
    const oldGrid = document.getElementById('packs-grid'); // For backward compatibility
    
    if (!activeGrid && !inactiveGrid && !oldGrid) {
        console.warn('No packs container found');
        return;
    }
    
    try {
        const res = await fetch('/api/v1/packs/');
        if (!res.ok) throw new Error('Failed to fetch packs');
        const data = await res.json();
        const packs = data.packs || [];
        
        // Separate active and inactive packs
        const active = packs.filter(p => p.is_active);
        const inactive = packs.filter(p => !p.is_active);
        
        // Update active packs list
        if (activeGrid) {
            if (active.length > 0) {
                activeGrid.innerHTML = active.map(p => `
                    <div style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #34d399; margin-bottom: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight:700; color:#38bdf8;">${p.name}</span>
                            <span class="tag tag-success">Active</span>
                        </div>
                        <div style="color:#94a3b8; font-size: 12px; margin-bottom: 10px;">Domain: ${p.domain} | Version: ${p.version}</div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn" style="background: #fbbf24; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="togglePack('${p.id}')">Deactivate</button>
                            <button class="btn" style="background: #f87171; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="removePack('${p.id}')">Remove</button>
                        </div>
                    </div>
                `).join('');
            } else {
                activeGrid.innerHTML = '<div style="padding: 20px; text-align: center; color: #64748b;">No active packs</div>';
            }
        }
        
        // Update inactive packs list
        if (inactiveGrid) {
            if (inactive.length > 0) {
                inactiveGrid.innerHTML = inactive.map(p => `
                    <div style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid #f87171; margin-bottom: 10px;">
                        <div style="display:flex; justify-content:space-between; align-items: center; margin-bottom: 10px;">
                            <span style="font-weight:700; color:#94a3b8;">${p.name}</span>
                            <span class="tag tag-danger">Inactive</span>
                        </div>
                        <div style="color:#94a3b8; font-size: 12px; margin-bottom: 10px;">Domain: ${p.domain} | Version: ${p.version}</div>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn" style="background: #34d399; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="togglePack('${p.id}')">Activate</button>
                            <button class="btn" style="background: #f87171; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="removePack('${p.id}')">Remove</button>
                        </div>
                    </div>
                `).join('');
            } else {
                inactiveGrid.innerHTML = '<div style="padding: 20px; text-align: center; color: #64748b;">No inactive packs</div>';
            }
        }
        
        // Also handle old packs-grid if it exists (backward compatibility)
        if (oldGrid) {
            oldGrid.innerHTML = packs.map(p => `
                <div style="background: #1e293b; padding: 15px; border-radius: 8px; border-left: 4px solid ${p.is_active ? '#34d399' : '#f87171'}; margin-bottom: 10px;">
                    <div style="display:flex; justify-content:space-between; align-items: center; margin-bottom: 10px;">
                        <span style="font-weight:700; color:#38bdf8;">${p.name}</span>
                        <span class="tag ${p.is_active ? 'tag-success' : 'tag-danger'}">${p.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div style="color:#94a3b8; font-size: 12px; margin-bottom: 10px;">Domain: ${p.domain} | Version: ${p.version}</div>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn" style="background: ${p.is_active ? '#fbbf24' : '#34d399'}; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="togglePack('${p.id}')">
                            ${p.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        <button class="btn" style="background: #f87171; padding: 5px 10px; font-size: 11px; cursor: pointer;" onclick="removePack('${p.id}')">Remove</button>
                    </div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Error loading packs:', e);
        const target = document.getElementById('active-packs-list') || document.getElementById('packs-grid');
        if (target) target.innerHTML = '<div style="color: #f87171; padding: 20px;">Error loading packs</div>';
    }
}

// ============ TOGGLE PACK ============
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

// ============ REMOVE PACK ============
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

// ============ INSTALL PACK ============
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

// ============ BULK TOGGLE ============
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

// Make functions globally accessible
window.fetchPacks = fetchPacks;
window.togglePack = togglePack;
window.removePack = removePack;
window.installPack = installPack;
window.bulkTogglePacks = bulkTogglePacks;

console.log('✅ packs.js loaded');
