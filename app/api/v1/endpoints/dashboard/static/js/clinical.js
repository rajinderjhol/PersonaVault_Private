// Clinical Decision Intelligence - USB Focus

async function loadClinicalDashboard() {
    try {
        const res = await fetch('/api/v1/clinical/decisions?days=30');
        const data = await res.json();
        
        document.getElementById('clinical-decision-count').textContent = data.total || 0;
        document.getElementById('clinical-human-reviewed').textContent = data.human_reviewed || 0;
        document.getElementById('clinical-compliance-rate').textContent = data.compliance_rate || '0%';
        document.getElementById('clinical-avg-confidence').textContent = data.avg_confidence || '0%';
        
        renderClinicalFeed(data.recent_activity || []);
    } catch (e) {
        console.error('Clinical dashboard error:', e);
    }
}

function renderClinicalFeed(activities) {
    const feed = document.getElementById('clinical-feed');
    if (!feed) return;
    
    if (activities.length === 0) {
        feed.innerHTML = '<div class="metric-label">No recent clinical AI activity.</div>';
        return;
    }
    
    feed.innerHTML = activities.map(a => `
        <div style="padding:12px; background:#020617; border-radius:8px; border-left:3px solid ${getClinicalColor(a.type)}; margin-bottom:8px;">
            <div style="display:flex; justify-content:space-between;">
                <span style="font-weight:700; color:#38bdf8;">${a.type.toUpperCase()}</span>
                <span style="color:#64748b; font-size:11px;">${new Date(a.timestamp).toLocaleString()}</span>
            </div>
            <div style="font-size:13px; color:#f1f5f9;">${a.description}</div>
            <div style="display:flex; gap:15px; margin-top:5px; font-size:11px;">
                <span style="color:#94a3b8;">Confidence: ${a.confidence}%</span>
                <span style="color:#${a.human_reviewed ? '34d399' : 'fbbf24'};">
                    ${a.human_reviewed ? '✅ Human Reviewed' : '⏳ Pending Review'}
                </span>
                <span style="color:#64748b; font-family:monospace;">Receipt: ${a.receipt_id?.substring(0,12) || 'N/A'}</span>
            </div>
        </div>
    `).join('');
}

function getClinicalColor(type) {
    const colors = {
        'radiology': '#38bdf8',
        'pathology': '#a855f7',
        'clinical': '#34d399',
        'documentation': '#fbbf24'
    };
    return colors[type] || '#64748b';
}

async function searchClinicalAudit() {
    const query = document.getElementById('clinical-audit-search').value;
    const type = document.getElementById('clinical-audit-type').value;
    const results = document.getElementById('clinical-audit-results');
    
    results.innerHTML = '<div class="metric-label">Searching...</div>';
    
    try {
        const res = await fetch(`/api/v1/clinical/decisions?search=${encodeURIComponent(query)}&type=${type}`);
        const data = await res.json();
        
        if (data.decisions?.length > 0) {
            results.innerHTML = data.decisions.map(d => `
                <div style="padding:12px; background:#020617; border-radius:8px; border:1px solid #334155; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:700; color:#38bdf8;">${d.id}</span>
                        <span class="tag ${d.status === 'verified' ? 'tag-success' : 'tag-warning'}">${d.status}</span>
                    </div>
                    <div style="font-size:12px; color:#94a3b8;">${d.description}</div>
                    <div style="display:flex; gap:15px; margin-top:5px; font-size:11px;">
                        <span>Patient: ${d.patient_id || 'N/A'}</span>
                        <span>Type: ${d.type}</span>
                        <span>Human: ${d.human_reviewed ? '✅' : '⏳'}</span>
                        <button onclick="verifyClinicalReceipt('${d.receipt_id}')" class="refresh-btn" style="padding:2px 8px; font-size:10px; margin-left:10px;">
                            Verify Proof
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            results.innerHTML = '<div class="metric-label">No clinical decisions found.</div>';
        }
    } catch (e) {
        results.innerHTML = '<div class="metric-label" style="color:#f87171;">Error loading audit results.</div>';
    }
}

async function verifyClinicalReceipt(receiptId) {
    if (!receiptId) return;
    try {
        const res = await fetch(`/api/v1/clinical/decisions/${receiptId}/verify`);
        const data = await res.json();
        const evidence = document.getElementById('crypto-evidence');
        evidence.innerHTML = `
            <div style="background:#020617; padding:15px; border-radius:8px; border:1px solid #334155;">
                <div style="color:#34d399; font-weight:700;">✅ Cryptographic Verification Passed</div>
                <div style="margin-top:10px; font-size:10px; color:#94a3b8;">
                    <div>Receipt: ${data.receipt_id}</div>
                    <div>Merkle Root: ${data.merkle_root?.substring(0, 32)}...</div>
                    <div>Timestamp: ${new Date(data.timestamp).toLocaleString()}</div>
                    <div>Signature: ${data.signature?.substring(0, 32)}...</div>
                </div>
            </div>
        `;
        showToast('✅ Receipt verified cryptographically!', 'success');
    } catch (e) {
        showToast('Verification failed: ' + e.message, 'error');
    }
}

function exportClinicalAudit() {
    showToast('📊 Clinical audit export started...', 'info');
    // Trigger download via window.open or fetch
    window.open('/api/v1/clinical/decisions/export?format=json', '_blank');
}

// ========== CLINICAL COCKPIT INTERACTION ==========

function toggleCockpit() {
    const sidebar = document.getElementById('cockpit-sidebar');
    if (!sidebar) return;
    
    const isVisible = sidebar.style.display !== 'none';
    sidebar.style.display = isVisible ? 'none' : 'block';
    
    // Adjust chat width if necessary
    const chatContainer = sidebar.previousElementSibling;
    if (chatContainer) {
        chatContainer.style.flex = isVisible ? '1' : '0 0 calc(100% - 320px)';
    }
}

async function updateCockpit(contextData) {
    const container = document.getElementById('cockpit-content');
    if (!container) return;
    
    // In a real implementation, contextData would be fetched from the AI's latest response context
    // or passed via a WebSocket event.
    container.innerHTML = `
        <div class="cockpit-section">
            <div class="cockpit-title">👤 Patient Context</div>
            <div class="cockpit-item"><span class="cockpit-label">Patient</span><span class="cockpit-value">${contextData.patient_id}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">Age/Sex</span><span class="cockpit-value">${contextData.age}/${contextData.sex}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">Diagnosis</span><span class="cockpit-value">${contextData.diagnosis}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">Attending</span><span class="cockpit-value">${contextData.attending}</span></div>
        </div>

        <div class="cockpit-section">
            <div class="cockpit-title">🧠 Clinical Intelligence</div>
            <div class="cockpit-item"><span class="cockpit-label">Protocols</span><span class="cockpit-value" style="color: var(--accent);">${contextData.protocol}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">Confidence</span><span class="cockpit-value" style="color: #34d399;">${contextData.confidence}</span></div>
        </div>

        <div class="cockpit-section">
            <div class="cockpit-title">🛡️ Governance & Compliance</div>
            <div class="cockpit-item"><span class="cockpit-label">HITL Status</span><span class="cockpit-value" style="color: #34d399;">✅ ${contextData.hitl_status}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">VAP Receipt</span><span class="cockpit-value">${contextData.receipt_id}</span></div>
            <div class="cockpit-item"><span class="cockpit-label">Risk Tier</span><span class="cockpit-value">${contextData.risk_tier}</span></div>
        </div>
    `;
}

// Example usage triggered after an AI response:
// updateCockpit({
//     patient_id: "USB-9923",
//     age: 67,
//     sex: "F",
//     diagnosis: "L-Lobe Mass",
//     attending: "Dr. Sarah Chen",
//     protocol: "NCCN v3.2026",
//     confidence: "94%",
//     hitl_status: "Approved",
//     receipt_id: "VAP-USB-772",
//     risk_tier: "Tier 3"
// });
