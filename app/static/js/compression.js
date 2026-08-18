// ============ COMPRESSION DASHBOARD ============

async function loadCompressionStats() {
    const totalEl = document.getElementById('compression-total');
    if (!totalEl) return;

    try {
        const res = await fetch('/api/v1/admin/dashboard/compression/metrics');
        if (!res.ok) throw new Error('Failed to fetch metrics');
        const data = await res.json();
        
        const activeEl = document.getElementById('compression-active');
        const ratioEl = document.getElementById('compression-ratio');
        const progressEl = document.getElementById('compression-progress');
        const successEl = document.getElementById('compression-success');
        
        if (totalEl) totalEl.textContent = data.patterns_count?.total || 0;
        if (activeEl) activeEl.textContent = data.patterns_count?.active || 0;
        if (ratioEl) ratioEl.textContent = (data.compression_ratio || 0) + ':1';
        if (progressEl) progressEl.textContent = (data.progress_percent || 0).toFixed(1) + '%';
        if (successEl) successEl.textContent = (data.success_rate || 0) + '%';
        
        // Update reinforcement avg weight
        document.getElementById('reinforcement-avg-weight').textContent = (data.avg_pattern_weight || 0).toFixed(2);
        
        // Update pattern feed
        const feed = document.getElementById('pattern-feed');
        if (feed && data.patterns && data.patterns.length > 0) {
            feed.innerHTML = data.patterns.map(p => `
                <div style="padding: 8px; background: #020617; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid ${p.weight > 0.7 ? '#34d399' : p.weight > 0.4 ? '#fbbf24' : '#f87171'};">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #38bdf8; font-weight: 600;">${p.pattern_type || 'Unknown'}</span>
                        <span style="color: #94a3b8; font-size: 11px;">Weight: ${(p.weight || 0).toFixed(2)}</span>
                        <span class="tag ${p.is_active ? 'tag-success' : 'tag-danger'}" style="font-size: 9px; padding: 2px 6px;">${p.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Trigger: ${p.trigger || 'N/A'}</div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Compression metrics error:', e);
    }
}

// Added to fix ReferenceError
async function loadCompressionMetrics() {
    return loadCompressionStats();
}

async function compressSource(sourceType, data) {
    const status = document.getElementById('compress-status');
    const result = document.getElementById('compress-result');
    if (!status) return;

    status.textContent = `⏳ Compressing ${sourceType}...`;
    result.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/compression/compress', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_type: sourceType, data: data })
        });
        
        const response = await res.json();
        status.textContent = `✅ Compressed ${sourceType}: ${response.patterns_extracted || 0} patterns extracted`;
        
        result.style.display = 'block';
        result.innerHTML = `
            <div style="color: #34d399;">✅ Compression complete</div>
            <div style="color: #94a3b8; margin-top: 4px;">Patterns extracted: ${response.patterns_extracted || 0}</div>
            <div style="color: #94a3b8; margin-top: 4px;">Patterns saved: ${response.patterns_saved || 0}</div>
            <div style="color: #94a3b8; margin-top: 4px;">Compression ratio: ${response.compression_ratio || 0}:1</div>
            <div style="color: #64748b; margin-top: 4px; font-size: 11px;">Time: ${(response.duration_ms || 0).toFixed(0)}ms</div>
        `;
        
        loadAllMetrics();
    } catch (e) {
        status.textContent = `❌ Error: ${e.message}`;
    }
}

function compressDocument() {
    const data = {
        title: "Sample Document",
        content: "This is a sample document for testing compression. It contains contract review notes, security policies, and compliance requirements."
    };
    compressSource('document', data);
}

function compressConversation() {
    const data = [
        { content: "Tell me about the contracts?" },
        { content: "We have several contracts with different vendors." },
        { content: "What about the security policies?" }
    ];
    compressSource('conversation', data);
}

function compressDecision() {
    const data = {
        id: 1,
        query: "Should we approve the vendor contract?",
        outcome: "success",
        confidence: 0.92
    };
    compressSource('decision', data);
}

function compressFeedback() {
    const data = {
        rating: 5,
        comment: "Great response! Very helpful information about the contracts."
    };
    compressSource('feedback', data);
}

// ============ DOMAIN TRANSFER FUNCTIONS ============

async function transferDomain() {
    const source = document.getElementById('source-domain-select').value;
    const target = document.getElementById('target-domain-select').value;
    const status = document.getElementById('compress-status');
    const result = document.getElementById('transfer-result');
    if (!status) return;
    
    status.textContent = `⏳ Transferring patterns from ${source} to ${target}...`;
    result.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/transfer/domain', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_domain: source, target_domain: target, limit: 20 })
        });
        
        const data = await res.json();
        status.textContent = `✅ Transferred ${data.transferred || 0} patterns from ${source} to ${target}`;
        
        result.style.display = 'block';
        result.innerHTML = `
            <div style="color: #8b5cf6;">🔄 Transfer complete</div>
            <div style="color: #94a3b8; margin-top: 4px;">Source: ${source} → Target: ${target}</div>
            <div style="color: #34d399; margin-top: 4px;">Patterns transferred: ${data.transferred || 0}</div>
            ${data.patterns ? data.patterns.map(p => `
                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">- ${p.trigger}</div>
            `).join('') : ''}
        `;
        
        loadAllMetrics();
    } catch (e) {
        status.textContent = `❌ Error: ${e.message}`;
    }
}

async function transferAllDomains() {
    const status = document.getElementById('compress-status');
    const result = document.getElementById('transfer-result');
    if (!status) return;
    
    if (!confirm('Transfer patterns across all domain pairs? This may take a moment.')) return;
    
    status.textContent = '⏳ Transferring across all domains...';
    result.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/transfer/all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        status.textContent = `✅ Transferred ${data.total_transfers || 0} patterns across ${data.domain_pairs || 0} domain pairs`;
        
        result.style.display = 'block';
        result.innerHTML = `
            <div style="color: #8b5cf6;">🌐 Cross-domain transfer complete</div>
            <div style="color: #34d399; margin-top: 4px;">Total transfers: ${data.total_transfers || 0}</div>
            <div style="color: #94a3b8; margin-top: 4px;">Domain pairs: ${data.domain_pairs || 0}</div>
            ${data.results ? Object.entries(data.results).map(([pair, r]) => `
                <div style="font-size: 11px; color: #64748b; margin-top: 2px;">${pair}: ${r.transferred || 0} patterns</div>
            `).join('') : ''}
        `;
        
        loadAllMetrics();
    } catch (e) {
        status.textContent = `❌ Error: ${e.message}`;
    }
}

// Load reinforcement stats on page load
async function loadReinforcementStats() {
    const activeEl = document.getElementById('reinforcement-active');
    if (!activeEl) return;

    try {
        const res = await fetch('/api/v1/admin/dashboard/reinforcement/stats');
        if (!res.ok) throw new Error('Failed to fetch reinforcement stats');
        const data = await res.json();
        
        const successRateEl = document.getElementById('reinforcement-success-rate');
        const avgWeightEl = document.getElementById('reinforcement-avg-weight');
        const decayedEl = document.getElementById('reinforcement-decayed');
        
        // Calculate success rate
        const successRate = data.history_count > 0 ? 
            (data.successful_reinforcements / data.history_count * 100).toFixed(1) : 0;
        
        if (successRateEl) successRateEl.textContent = successRate + '%';
        if (avgWeightEl) avgWeightEl.textContent = (data.avg_weight || 0).toFixed(2);
        if (decayedEl) decayedEl.textContent = data.decayed_count || 0;
        
    } catch (e) {
        console.error('Reinforcement stats error:', e);
    }
}

async function runDecay() {
    const status = document.getElementById('compress-status');
    const result = document.getElementById('decay-result');
    if (!status) return;
    
    status.textContent = '⏳ Running pattern decay...';
    result.style.display = 'none';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/reinforcement/decay', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        status.textContent = '✅ Decay complete';
        
        result.style.display = 'block';
        result.innerHTML = `
            <div style="color: #34d399;">✅ Decay completed</div>
            <div style="color: #94a3b8; margin-top: 4px;">Patterns checked: ${data.patterns_checked || 0}</div>
            <div style="color: #94a3b8; margin-top: 4px;">Patterns decayed: ${data.patterns_decayed || 0}</div>
            <div style="color: #f87171; margin-top: 4px;">Patterns deactivated: ${data.patterns_deactivated || 0}</div>
        `;
        
        loadAllMetrics();
    } catch (e) {
        status.textContent = `❌ Error: ${e.message}`;
    }
}

async function takeSnapshot() {
    const status = document.getElementById('compress-status');
    if (!status) return;
    
    status.textContent = '⏳ Taking snapshot...';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/compression/snapshot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await res.json();
        status.textContent = `✅ Snapshot taken: ${data.compression_ratio}:1 ratio, ${data.patterns_count} patterns`;
        loadAllMetrics();
    } catch (e) {
        status.textContent = `❌ Error: ${e.message}`;
    }
}

async function loadCompressionChart(days) {
    const ctxEl = document.getElementById('compression-chart');
    if (!ctxEl) return;
    
    currentDays = days || currentDays;
    try {
        const res = await fetch(`/api/v1/admin/dashboard/compression/timeline?days=${currentDays}`);
        if (!res.ok) throw new Error('Failed to fetch timeline');
        const data = await res.json();
        
        const ctx = ctxEl.getContext('2d');
        
        if (compressionChart) {
            compressionChart.destroy();
        }
        
        const labels = data.map(d => new Date(d.timestamp).toLocaleDateString());
        const ratios = data.map(d => d.compression_ratio);
        const patterns = data.map(d => d.patterns_count);
        
        compressionChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Compression Ratio',
                        data: ratios,
                        borderColor: '#a855f7',
                        backgroundColor: 'rgba(168, 85, 247, 0.1)',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Patterns',
                        data: patterns,
                        borderColor: '#38bdf8',
                        backgroundColor: 'rgba(56, 189, 248, 0.1)',
                        fill: true,
                        tension: 0.3,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#64748b', maxTicksLimit: 15 }, grid: { color: '#1e293b' } },
                    y: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#64748b' },
                        grid: { color: '#1e293b' }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        ticks: { color: '#64748b' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
        
    } catch (e) {
        console.error('Chart error:', e);
    }
}

async function loadCompressionBreakdown() {
    const rawEl = document.getElementById('breakdown-raw');
    if (!rawEl) return;
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/compression/breakdown');
        if (!res.ok) throw new Error('Failed to fetch breakdown');
        const data = await res.json();
        
        rawEl.textContent = data.raw_data?.total_tokens || 0;
        document.getElementById('breakdown-compressed').textContent = data.compressed?.patterns || 0;
        
        const savings = data.raw_data?.total_tokens > 0 ? 
            (1 - (data.compressed?.patterns || 0) / data.raw_data?.total_tokens) * 100 : 0;
        document.getElementById('breakdown-savings').textContent = savings.toFixed(1) + '%';
        document.getElementById('breakdown-weight').textContent = (data.compressed?.avg_weight || 0).toFixed(2);
        
    } catch (e) {
        console.error('Breakdown error:', e);
    }
}

async function loadPatternFeed() {
    const feed = document.getElementById('pattern-feed');
    if (!feed) return;
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/compression/metrics');
        if (!res.ok) throw new Error('Failed to fetch patterns');
        const data = await res.json();
        
        const patterns = data.patterns || [];
        
        if (patterns && patterns.length > 0) {
            feed.innerHTML = patterns.slice(0, 20).map(p => `
                <div style="padding: 8px; background: #020617; border-radius: 6px; margin-bottom: 6px; border-left: 3px solid ${p.weight > 0.7 ? '#34d399' : p.weight > 0.4 ? '#fbbf24' : '#f87171'};">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="color: #38bdf8; font-weight: 600;">${p.pattern_type || 'Unknown'}</span>
                        <span style="color: #94a3b8; font-size: 11px;">Weight: ${(p.weight || 0).toFixed(2)}</span>
                        <span class="tag ${p.is_active ? 'tag-success' : 'tag-danger'}" style="font-size: 9px; padding: 2px 6px;">${p.is_active ? 'Active' : 'Inactive'}</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">Trigger: ${p.trigger || 'N/A'}</div>
                </div>
            `).join('');
        }
    } catch (e) {
        console.error('Pattern feed error:', e);
    }
}

// ============ EXPORT/IMPORT FUNCTIONS ============

async function exportPatterns() {
    const domain = document.getElementById('export-domain').value;
    const minWeight = parseFloat(document.getElementById('export-min-weight').value) || 0;
    const result = document.getElementById('export-result');
    
    result.textContent = '⏳ Exporting patterns...';
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/patterns/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ domain: domain || null, min_weight: minWeight })
        });
        
        const data = await res.json();
        result.textContent = `✅ Exported ${data.count || 0} patterns`;
        
        // Show package preview
        const packageEl = document.getElementById('import-package');
        if (packageEl) {
            packageEl.value = data.package;
        }
        
    } catch (e) {
        result.textContent = `❌ Error: ${e.message}`;
    }
}

async function downloadPatterns() {
    const domain = document.getElementById('export-domain').value;
    const minWeight = parseFloat(document.getElementById('export-min-weight').value) || 0;
    
    let url = '/api/v1/admin/dashboard/patterns/export/download';
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    params.append('min_weight', minWeight);
    if (params.toString()) url += '?' + params.toString();
    
    window.open(url, '_blank');
}

async function importPatterns() {
    const packageText = document.getElementById('import-package').value;
    const merge = document.getElementById('import-merge').checked;
    const validate = document.getElementById('import-validate').checked;
    const dryRun = document.getElementById('import-dry-run').checked;
    const result = document.getElementById('import-result');
    
    if (!packageText) {
        result.textContent = '❌ Please provide a pattern package';
        return;
    }
    
    try {
        JSON.parse(packageText);
    } catch (e) {
        result.textContent = '❌ Invalid JSON format';
        return;
    }
    
    result.textContent = `⏳ Importing patterns (dry run: ${dryRun})...`;
    
    try {
        const res = await fetch('/api/v1/admin/dashboard/patterns/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                package: packageText,
                merge: merge,
                validate: validate,
                dry_run: dryRun
            })
        });
        
        const data = await res.json();
        
        if (data.success) {
            const stats = data.stats || {};
            result.textContent = `✅ Imported: ${stats.imported || 0}, Skipped: ${stats.skipped || 0}, Errors: ${stats.errors || 0}`;
            if (!dryRun) loadAllMetrics();
        } else {
            result.textContent = `❌ Import failed: ${data.error || 'Unknown error'}`;
        }
    } catch (e) {
        result.textContent = `❌ Error: ${e.message}`;
    }
}

function clearImport() {
    document.getElementById('import-package').value = '';
    document.getElementById('import-result').textContent = 'Cleared';
}

async function loadAllMetrics() {
    await Promise.all([
        loadCompressionMetrics(),
        loadCompressionChart(currentDays),
        loadCompressionBreakdown(),
        loadPatternFeed(),
        loadReinforcementStats()
    ]);
}

// Init
let compressionChart = null;
let currentDays = 30;
setTimeout(loadAllMetrics, 500);
