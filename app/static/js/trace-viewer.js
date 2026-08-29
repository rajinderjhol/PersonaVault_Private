/**
 * Decision Trace Viewer - Pure JavaScript
 * Fetches and renders collapsible decision traces
 */
class DecisionTraceViewer {
    constructor(containerId, traceId, options = {}) {
        this.containerId = containerId;
        this.traceId = traceId;
        this.isExpanded = options.isExpanded || false;
        this.trace = null;
        this.container = null;
        this.error = null;
        this.loading = true;
    }

    async render() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`Container #${this.containerId} not found`);
            return;
        }

        this.showLoading();
        await this.fetchTrace();
        this.renderTrace();
    }

    showLoading() {
        this.container.innerHTML = `<div class="trace-loading">⏳ Loading trace...</div>`;
    }

    async fetchTrace() {
        try {
            const response = await fetch(`/api/v1/traces/${this.traceId}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            this.trace = await response.json();
            this.loading = false;
        } catch (err) {
            this.error = err.message;
            this.loading = false;
            console.error('Failed to fetch trace:', err);
        }
    }

    renderTrace() {
        if (this.loading) {
            this.container.innerHTML = `<div class="trace-loading">⏳ Loading trace...</div>`;
            return;
        }

        if (this.error || !this.trace) {
            this.container.innerHTML = `<div class="trace-error">⚠️ ${this.error || 'Unable to load trace'}</div>`;
            return;
        }

        const stepConfig = this.getStepConfig(this.trace.step);
        const confidence = this.trace.confidence_score !== null 
            ? Math.round(this.trace.confidence_score * 100) 
            : 'N/A';
        const confidenceClass = this.getConfidenceClass(this.trace.confidence_score);

        const provenanceHtml = this.trace.provenance_links?.length > 0 
            ? this.renderProvenance(this.trace.provenance_links)
            : '';

        this.container.innerHTML = `
            <div class="trace-card ${stepConfig.color}">
                <div class="trace-header" onclick="window.toggleTrace('${this.containerId}')">
                    <div class="trace-header-left">
                        <span class="trace-icon">${stepConfig.icon}</span>
                        <div>
                            <div class="trace-step-label">${stepConfig.label}</div>
                            <div class="trace-step-description">${stepConfig.description}</div>
                        </div>
                        ${this.trace.is_crystallized ? '<span class="trace-badge">🧊 Crystallized</span>' : ''}
                        ${this.trace.confidence_score !== null ? `
                            <span class="trace-confidence ${confidenceClass}">${confidence}%</span>
                        ` : ''}
                    </div>
                    <div class="trace-header-right">
                        <span class="trace-time">${new Date(this.trace.timestamp).toLocaleTimeString()}</span>
                        <span class="trace-toggle ${this.isExpanded ? 'expanded' : ''}">▼</span>
                    </div>
                </div>
                <div class="trace-body ${this.isExpanded ? 'expanded' : ''}">
                    <div class="trace-data">
                        <h4 class="trace-section-title">Step Data</h4>
                        <pre class="trace-json">${this.safeJsonStringify(this.trace.data)}</pre>
                    </div>
                    ${provenanceHtml}
                    ${!this.trace.is_crystallized ? `
                        <button class="trace-crystallize-btn" onclick="window.crystallizeTrace('${this.trace.id}')">
                            🧊 Crystallize this decision pattern
                        </button>
                    ` : ''}
                </div>
            </div>
        `;

        window.traceInstances = window.traceInstances || {};
        window.traceInstances[this.containerId] = this;
    }

    renderProvenance(links) {
        return `
            <div class="trace-provenance">
                <h4 class="trace-section-title">📎 Provenance (${links.length})</h4>
                ${links.map(link => `
                    <div class="trace-provenance-item">
                        <span class="trace-provenance-type">${link.source_type}</span>
                        <span class="trace-provenance-text">${link.source_text || ''}</span>
                        ${link.relevance_score !== null ? `
                            <span class="trace-provenance-score">${Math.round(link.relevance_score * 100)}%</span>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        `;
    }

    safeJsonStringify(obj) {
        try {
            return JSON.stringify(obj, null, 2);
        } catch (e) {
            return String(obj);
        }
    }

    toggle() {
        this.isExpanded = !this.isExpanded;
        const body = this.container?.querySelector('.trace-body');
        const toggle = this.container?.querySelector('.trace-toggle');
        if (body) {
            body.classList.toggle('expanded');
        }
        if (toggle) {
            toggle.classList.toggle('expanded');
        }
    }

    getStepConfig(step) {
        const configs = {
            perception: {
                label: '🔍 Perception',
                color: 'border-blue-300',
                icon: '🔍',
                description: 'Event identification and fact extraction'
            },
            policy_match: {
                label: '📋 Policy Match',
                color: 'border-purple-300',
                icon: '📋',
                description: 'Verifiable policies applied'
            },
            ai_recommendation: {
                label: '🤖 AI Recommendation',
                color: 'border-green-300',
                icon: '🤖',
                description: 'AI suggested action within policy bounds'
            },
            action: {
                label: '⚡ Action',
                color: 'border-orange-300',
                icon: '⚡',
                description: 'Decision made with verifiable path'
            },
            outcome: {
                label: '✅ Outcome',
                color: 'border-teal-300',
                icon: '✅',
                description: 'Result with full auditable trace'
            },
            summary: {
                label: '📊 Summary',
                color: 'border-gray-300',
                icon: '📊',
                description: 'Top-level decision summary'
            }
        };
        return configs[step] || configs.summary;
    }

    getConfidenceClass(score) {
        if (score === null) return 'confidence-unknown';
        if (score > 0.8) return 'confidence-high';
        if (score > 0.5) return 'confidence-medium';
        return 'confidence-low';
    }
}

// Global functions
window.toggleTrace = function(containerId) {
    const instance = window.traceInstances?.[containerId];
    if (instance) {
        instance.toggle();
    } else {
        console.warn(`Trace instance not found for: ${containerId}`);
    }
};

window.crystallizeTrace = async function(traceId) {
    if (!confirm('Mark this decision pattern as crystallized? This will enable faster future responses.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/traces/${traceId}/crystallize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (response.ok) {
            alert('✅ Trace crystallized successfully!');
            // Refresh the page to show updated state
            location.reload();
        } else {
            const error = await response.json();
            alert(`❌ Failed to crystallize: ${error.detail || 'Unknown error'}`);
        }
    } catch (err) {
        console.error('Failed to crystallize trace:', err);
        alert('❌ Error crystallizing trace');
    }
};

// Auto-initialize trace viewers on page load
document.addEventListener('DOMContentLoaded', function() {
    const viewers = document.querySelectorAll('[data-trace-viewer]');
    if (viewers.length === 0) {
        console.log('No trace viewers found on page');
        return;
    }
    
    console.log(`Initializing ${viewers.length} trace viewer(s)...`);
    viewers.forEach(el => {
        const traceId = el.dataset.traceId;
        if (!traceId) {
            console.warn('Trace viewer missing data-trace-id:', el);
            return;
        }
        
        const containerId = el.id || `trace-${traceId}`;
        if (!el.id) el.id = containerId;
        
        const viewer = new DecisionTraceViewer(containerId, traceId, { 
            isExpanded: false 
        });
        viewer.render();
    });
});
