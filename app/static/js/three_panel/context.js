/**
 * Context Panel - Dynamic right sidebar intelligence
 */

class ContextPanel {
    constructor() {
        this.currentDecision = null;
        this.metrics = null;
        this.transitions = [];
        this.snowflakes = [];
        this.updateInterval = null;
        this.ws = null;
        this.isRefreshing = false;
        this.init();
    }

    init() {
        console.log("ContextPanel: initializing...");
        this.loadContext();
        this.setupWebSocket();
        // Auto-refresh every 60 seconds
        this.updateInterval = setInterval(() => this.refreshAll(), 60000);
    }

    async refreshAll() {
        if (this.isRefreshing) {
            console.log('ContextPanel: refresh already in progress, skipping.');
            return;
        }
        this.isRefreshing = true;
        console.log("ContextPanel: refreshing...");
        await this.loadContext();
        this.isRefreshing = false;
    }

    async loadContext() {
        console.log("ContextPanel: loading context...");
        try {
            const [decision, metrics, transitions, snowflakes] = await Promise.all([
                this.loadCurrentDecision(),
                this.loadMetrics(),
                this.loadRecentTransitions(),
                this.loadActiveSnowflakes()
            ]);

            this.currentDecision = decision;
            this.metrics = metrics;
            this.transitions = transitions || [];
            this.snowflakes = snowflakes || [];
            console.log("ContextPanel: context loaded.", { decision, metrics, transitions, snowflakes });

            this.renderAll();
        } catch (error) {
            console.error('ContextPanel: Failed to load context:', error.message);
        }
    }

    renderAll() {
        this.renderDecision();
        this.renderPhaseDistribution();
        this.renderTransitions();
        this.renderSnowflakes();
    }

    // --- Current Decision ---
    async loadCurrentDecision() {
        try {
            const response = await fetch('/api/v1/thermodynamics/current-decision', { credentials: 'include' });
            if (response.ok) return await response.json();
        } catch (error) {
            console.error('Failed to load current decision:', error);
        }
        return null;
    }

    renderDecision() {
        const container = document.getElementById('context-decision');
        if (!container) return;

        if (!this.currentDecision) {
            container.innerHTML = `<div class="context-empty"><span class="empty-icon">🔍</span><p>No active decision</p></div>`;
            return;
        }

        const d = this.currentDecision;
        container.innerHTML = `
            <div class="decision-card">
                <div class="decision-header">
                    <span class="decision-step ${d.step || 'unknown'}">${d.step ? d.step.replace('_', ' ') : 'Unknown'}</span>
                    <span class="decision-confidence">${d.confidence || 0}%</span>
                </div>
                <div class="detail-row"><span class="label">Agent</span><span class="value">${d.agent || 'Unknown'}</span></div>
                <div class="detail-row"><span class="label">Policy</span><span class="value">${d.policy || 'N/A'}</span></div>
            </div>
            <div class="decision-trace" id="decision-trace">
                <!-- Reasoning Trace injected here -->
            </div>
        `;
        
        // Render Reasoning Trace
        this.renderReasoningTrace(d.reasoningTrace);
    }

    renderReasoningTrace(trace) {
        const container = document.getElementById('decision-trace');
        if (!container || !trace) return;

        container.innerHTML = trace.map(step => `
            <div class="trace-step">
                <span class="step-icon">${step.status === 'complete' ? '✅' : '⏳'}</span>
                <span class="step-label">${step.title}</span>
                <span class="step-status">${step.summary}</span>
            </div>
        `).join('');
    }

    renderTraceSteps(trace) {
        const steps = ['perception', 'policy_match', 'ai_recommendation', 'action', 'outcome'];
        const icons = { perception: '🔍', policy_match: '📋', ai_recommendation: '🤖', action: '⚡', outcome: '✅' };
        return `
            <div class="decision-trace">
                ${steps.map(step => `
                    <div class="trace-step">
                        <span class="step-icon">${icons[step] || '📄'}</span>
                        <span class="step-label">${step.replace('_', ' ')}</span>
                        <span class="step-status ${trace[step] ? 'complete' : 'pending'}">${trace[step] ? '✅' : '⏳'}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // --- Phase Distribution ---
    async loadMetrics() {
        try {
            const response = await fetch('/api/v1/thermodynamics/phase-distribution', { credentials: 'include' });
            if (response.ok) return await response.json();
        } catch (error) {
            console.error('Failed to load metrics:', error);
        }
        return { gas: 0, liquid: 0, ice: 0, snowflake: 0 };
    }

    renderPhaseDistribution() {
        const data = this.metrics || { gas: 0, liquid: 0, ice: 0, snowflake: 0 };
        const total = data.gas + data.liquid + data.ice + data.snowflake || 1;
        
        const phases = [
            { id: 'gas', count: data.gas || 0 },
            { id: 'liquid', count: data.liquid || 0 },
            { id: 'ice', count: data.ice || 0 },
            { id: 'snowflake', count: data.snowflake || 0 }
        ];

        phases.forEach(phase => {
            const countEl = document.getElementById(`phase-${phase.id}`);
            const fillEl = document.getElementById(`phase-${phase.id}-fill`);
            if (countEl) countEl.textContent = phase.count;
            if (fillEl) {
                const pct = Math.max((phase.count / total) * 100, 0.5);
                fillEl.style.width = `${Math.min(pct, 100)}%`;
            }
        });
    }

    // --- Recent Transitions ---
    async loadRecentTransitions() {
        try {
            const response = await fetch('/api/v1/thermodynamics/transitions?limit=5', { credentials: 'include' });
            if (response.ok) return await response.json();
        } catch (error) {
            console.error('Failed to load transitions:', error);
        }
        return [];
    }

    renderTransitions() {
        const container = document.getElementById('thermo-transitions');
        if (!container) return;

        const transitions = this.transitions || [];
        if (transitions.length === 0) {
            container.innerHTML = `<div class="transition-empty">No recent transitions</div>`;
            return;
        }

        const icons = {
            freezing: '⬇️',
            melting: '🔥',
            evaporation: '💨',
            sublimation: '💨',
            snowflake: '❄️'
        };

        container.innerHTML = `
            <div class="transition-feed">
                ${transitions.slice(0, 5).map(t => `
                    <div class="transition-item ${t.type || ''}">
                        <span class="transition-icon">${t.icon || icons[t.type] || '🔄'}</span>
                        <span class="transition-desc">${t.description || t.type || 'Transition event'}</span>
                        <span class="transition-time">${t.timestamp || ''}</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // --- Active Snowflakes ---
    async loadActiveSnowflakes() {
        try {
            const response = await fetch('/api/v1/thermodynamics/snowflakes', { credentials: 'include' });
            if (response.ok) return await response.json();
        } catch (error) {
            console.error('Failed to load snowflakes:', error);
        }
        return [];
    }

    renderSnowflakes() {
        const container = document.getElementById('active-snowflakes');
        if (!container) return;

        const snowflakes = this.snowflakes || [];
        if (snowflakes.length === 0) {
            container.innerHTML = `<div class="snowflake-empty">No active snowflakes</div>`;
            return;
        }

        container.innerHTML = `
            <div class="snowflake-grid">
                ${snowflakes.slice(0, 3).map(s => `
                    <div class="snowflake-card-mini">
                        <div class="snowflake-name">❄️ ${s.domain.toUpperCase()}</div>
                        <div class="snowflake-focus">${s.focus || 'General'}</div>
                        <div class="snowflake-meta">
                            <span>${s.pattern_count || 0} patterns</span>
                            <span>${s.confidence || 0}%</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // --- WebSocket Setup ---
    setupWebSocket() {
        try {
            // Fix: Use WSS when site is loaded over HTTPS
            const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
            const clientId = 'v2_panel_' + Math.random().toString(36).substring(7);
            const wsUrl = `${protocol}://${window.location.host}/api/v1/thermodynamics/ws/${clientId}`;
            this.ws = new WebSocket(wsUrl);
            this.ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'transition') this.loadContext();
                else if (data.type === 'metrics') { this.metrics = data.data; this.renderPhaseDistribution(); }
                else if (data.type === 'decision') { this.currentDecision = data.data; this.renderDecision(); }
            };
        } catch (error) { console.warn('WebSocket error:', error); }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.contextPanel = new ContextPanel();
});
