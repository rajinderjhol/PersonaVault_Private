// Clinical Intelligence JavaScript
// Placeholder for clinical dashboard functionality

async function loadClinicalDashboard() {
    console.log('🏥 Loading clinical dashboard...');
    try {
        const res = await fetch('/api/v1/admin/dashboard/clinical/stats');
        const data = await res.json();
        
        // Update stats
        document.getElementById('clinical-decision-count').textContent = data.total_decisions || 0;
        document.getElementById('clinical-human-reviewed').textContent = data.human_reviewed || 0;
        document.getElementById('clinical-compliance-rate').textContent = (data.compliance_rate || 0) + '%';
        document.getElementById('clinical-avg-confidence').textContent = (data.avg_confidence || 0) + '%';
    } catch (e) {
        console.error('Clinical dashboard error:', e);
    }
}

async function searchClinicalAudit() {
    const searchTerm = document.getElementById('clinical-audit-search')?.value || '';
    const auditType = document.getElementById('clinical-audit-type')?.value || 'all';
    
    try {
        const res = await fetch(`/api/v1/admin/dashboard/clinical/audit?search=${encodeURIComponent(searchTerm)}&type=${auditType}`);
        const data = await res.json();
        const results = document.getElementById('clinical-audit-results');
        
        if (results && data.entries && data.entries.length > 0) {
            results.innerHTML = data.entries.map(entry => `
                <div style="padding:10px; background:#020617; border-radius:6px; margin-bottom:8px; border-left:4px solid #38bdf8;">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="font-weight:600; color:#38bdf8;">${entry.decision_type || 'Clinical Decision'}</span>
                        <span class="tag ${entry.status === 'approved' ? 'tag-success' : 'tag-warning'}">${entry.status || 'pending'}</span>
                    </div>
                    <div style="font-size:12px; color:#94a3b8;">Patient: ${entry.patient_id || 'N/A'} | Confidence: ${(entry.confidence || 0) * 100}%</div>
                    <div style="font-size:11px; color:#64748b; margin-top:4px;">Receipt: ${entry.receipt || 'No receipt'}</div>
                    <button class="btn" style="padding:2px 8px; font-size:10px; margin-top:5px;" onclick="verifyClinicalReceipt('${entry.receipt}')">
                        <i class="fas fa-check-circle"></i> Verify
                    </button>
                </div>
            `).join('');
        } else if (results) {
            results.innerHTML = '<div class="metric-label">No clinical audit entries found.</div>';
        }
    } catch (e) {
        console.error('Clinical audit search error:', e);
    }
}

async function verifyClinicalReceipt(receiptId) {
    if (!receiptId) return;
    try {
        const res = await fetch(`/api/v1/admin/dashboard/clinical/verify/${receiptId}`);
        const data = await res.json();
        
        if (data.valid) {
            showToast(`✅ Receipt ${receiptId} is valid`, 'success');
        } else {
            showToast(`❌ Receipt ${receiptId} is invalid`, 'error');
        }
    } catch (e) {
        showToast('Error verifying receipt', 'error');
    }
}

function exportClinicalAudit() {
    const searchTerm = document.getElementById('clinical-audit-search')?.value || '';
    const auditType = document.getElementById('clinical-audit-type')?.value || 'all';
    window.location.href = `/api/v1/admin/dashboard/clinical/export?search=${encodeURIComponent(searchTerm)}&type=${auditType}`;
}

console.log('✅ clinical.js loaded');
