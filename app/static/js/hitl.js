// HITL (Human-in-the-Loop) Functions
// This file contains all HITL-related functions for the dashboard

// ============ LOAD ACTIONS ============
async function loadActions() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/hitl/pending');
        if (!res.ok) throw new Error('Failed to fetch actions');
        const actions = await res.json();
        if (!Array.isArray(actions)) throw new Error('Invalid response format');
        
        const count = actions.length;
        const widget = document.getElementById('action-required-widget');
        if (!widget) return;
        
        const isManuallyClosed = sessionStorage.getItem('action-widget-closed') === 'true';
        const lastActionCount = parseInt(sessionStorage.getItem('last-action-count') || '0');

        if (count !== lastActionCount) {
            sessionStorage.setItem('action-widget-closed', 'false');
            sessionStorage.setItem('last-action-count', count.toString());
        }

        if (count > 0 && !isManuallyClosed) {
            widget.style.display = 'block';
            document.getElementById('action-count').textContent = count;
            document.getElementById('action-plural').textContent = count > 1 ? 's' : '';
            
            const list = document.getElementById('action-list');
            if (list) {
                let html = '';
                for (const a of actions) {
                    html += `
                        <div style="padding: 10px; background: #0f172a; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #f87171; display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <div style="font-weight: 600; color: #f1f5f9; font-size: 13px;">
                                    ${a.agent_type || 'Unknown Agent'}
                                    <span style="font-weight: 400; color: #94a3b8; font-size: 11px; margin-left: 8px;">
                                        ${new Date(a.timestamp).toLocaleTimeString()}
                                    </span>
                                </div>
                                <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                                    ${a.query || 'No description provided'}
                                </div>
                            </div>
                            <div style="display: flex; gap: 6px; margin-left: 10px; flex-shrink: 0;">
                                <button class="btn" style="padding: 2px 10px; font-size: 10px; background: #34d399; color: #0f172a; cursor: pointer;" onclick="resolveAction('${a.id}', 'approve')">
                                    Approve
                                </button>
                                <button class="btn" style="padding: 2px 10px; font-size: 10px; background: #f87171; cursor: pointer;" onclick="resolveAction('${a.id}', 'deny')">
                                    Deny
                                </button>
                                <button class="btn" style="padding: 2px 10px; font-size: 10px; background: #334155; cursor: pointer;" onclick="showHitlDetails('${a.id}')">
                                    Details
                                </button>
                            </div>
                        </div>
                    `;
                }
                list.innerHTML = html;
            }
        } else {
            widget.style.display = 'none';
        }
    } catch (e) {
        console.error('Actions load error:', e);
    }
}

// ============ RESOLVE ACTIONS ============
async function resolveAction(actionId, resolution) {
    try {
        const res = await fetch(`/api/v1/admin/dashboard/hitl/${actionId}/${resolution}`, { method: 'POST' });
        if (res.ok) {
            showToast('Action ' + resolution + 'd', 'success');
            loadActions();
            refreshContextBar();
        } else {
            showToast('Failed to resolve action', 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

async function approveAllActions() {
    if (!confirm('Approve all pending actions?')) return;
    try {
        const res = await fetch('/api/v1/admin/dashboard/hitl/approve-all', { method: 'POST' });
        if (res.ok) {
            showToast('All actions approved', 'success');
            loadActions();
            refreshContextBar();
        } else {
            showToast('Failed to approve all', 'error');
        }
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}

async function denyAllActions() {
    if (!confirm('Deny all pending actions?')) return;
    try {
        const res = await fetch('/api/v1/admin/dashboard/hitl/deny-all', { method: 'POST' });
        if (res.ok) {
            showToast('All actions denied', 'success');
            loadActions();
            refreshContextBar();
        } else {
            showToast('Failed to deny all', 'error');
        }
    } catch (e) { showToast('Error: ' + e.message, 'error'); }
}

function showHitlDetails(id) {
    const modal = document.getElementById('details-modal');
    const body = document.getElementById('modal-body');
    document.getElementById('modal-title').textContent = 'HITL Action Details';
    modal.style.display = 'block';
    body.innerHTML = '<div class="metric-label">Loading...</div>';
    fetch(`/api/v1/admin/dashboard/hitl/${id}/explain`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            body.innerHTML = `
                <div style="margin-bottom:15px;">
                    <div class="metric-label">Explanation</div>
                    <div style="background:#020617;padding:15px;border-radius:8px;margin-top:5px;">${data.explanation || 'No explanation available'}</div>
                </div>
                <button class="btn" onclick="closeModal()">Close</button>
            `;
        })
        .catch(() => {
            body.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading details</div>';
        });
}

function closeModal() {
    document.getElementById('details-modal').style.display = 'none';
}

console.log('✅ hitl.js loaded');
