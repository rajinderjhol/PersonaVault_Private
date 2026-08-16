// Pack Management UI Logic
async function fetchPacks() {
    const inactiveList = document.getElementById('inactive-packs-list');
    const activeList = document.getElementById('active-packs-list');
    if (!inactiveList || !activeList) return;
    
    inactiveList.innerHTML = '<div class="metric-label">Loading...</div>';
    activeList.innerHTML = '<div class="metric-label">Loading...</div>';
    
    try {
        // Cache-busting: add timestamp query param
        const res = await fetch(`/api/v1/packs/?t=${Date.now()}`);
        const data = await res.json();
        const packs = data.packs || []; 
        console.log("Fetched packs:", packs);
        
        const active = packs.filter(p => p.is_active);
        const inactive = packs.filter(p => !p.is_active);
        
        const renderPack = (p, isActive) => `
            <div style="background: #0f172a; padding: 10px; margin-bottom: 8px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-weight: 600; color: #38bdf8;">${p.name}</div>
                    <div style="font-size: 11px; color: #64748b;">${p.domain} v${p.version}</div>
                </div>
                <div style="display: flex; gap: 5px;">
                    <button class="btn" style="padding: 4px 8px; font-size: 10px; background: ${isActive ? '#fbbf24' : '#34d399'}" onclick="togglePack('${p.id}')">
                        ${isActive ? 'Deactivate' : 'Activate'}
                    </button>
                </div>
            </div>
        `;
        
        inactiveList.innerHTML = inactive.length ? inactive.map(p => renderPack(p, false)).join('') : '<div class="metric-label">No inactive packs</div>';
        activeList.innerHTML = active.length ? active.map(p => renderPack(p, true)).join('') : '<div class="metric-label">No active packs</div>';
        
    } catch (e) {
        inactiveList.innerHTML = '<div class="metric-label" style="color: #f87171;">Error loading packs</div>';
        activeList.innerHTML = '<div class="metric-label" style="color: #f87171;">Error loading packs</div>';
    }
}

async function togglePack(id) {
    try {
        const res = await fetch(`/api/v1/packs/${id}/toggle`, {method: 'POST'});
        if (res.ok) {
            await fetchPacks();
            showToast('Pack status updated', 'success');
        } else {
            throw new Error('Failed to toggle pack');
        }
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}

async function bulkTogglePacks(shouldDeactivate) {
    try {
        const res = await fetch(`/api/v1/packs/?t=${Date.now()}`);
        const data = await res.json();
        const packs = data.packs || [];
        // If shouldDeactivate is true, we want to deactivate currently active packs.
        // If shouldDeactivate is false, we want to activate currently inactive packs.
        const toToggle = packs.filter(p => p.is_active === !shouldDeactivate);
        
        for (const p of toToggle) {
            const response = await fetch(`/api/v1/packs/${p.id}/toggle`, {method: 'POST'});
            if (!response.ok) {
                console.error(`Failed to toggle pack ${p.id}`);
            }
        }
        
        await fetchPacks();
        showToast('Bulk update complete', 'success');
    } catch (e) { 
        console.error('Bulk toggle error:', e);
        showToast('Error during bulk update', 'error'); 
    }
}

async function removePack(id) {
    if (!confirm('Are you sure you want to remove this pack?')) return;
    try {
        const res = await fetch(`/api/v1/packs/${id}`, {method: 'DELETE'});
        if (res.ok) {
            fetchPacks();
            showToast('Pack removed', 'success');
        } else {
            throw new Error('Failed to remove pack');
        }
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}

async function installPack() {
    const fileInput = document.getElementById('pack-file-input');
    const status = document.getElementById('pack-install-status');
    const file = fileInput?.files?.[0];
    if (!file) { showToast('Select a YAML file', 'error'); return; }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        status.textContent = 'Installing...';
        const res = await fetch('/api/v1/packs/install', {method: 'POST', body: formData});
        if (res.ok) {
            status.textContent = '✅ Installed';
            fetchPacks();
        } else {
            throw new Error('Install failed');
        }
    } catch (e) {
        status.textContent = '❌ ' + e.message;
        showToast('Install failed', 'error');
    }
}
