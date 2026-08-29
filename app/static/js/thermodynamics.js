/**
 * ThermodynamicDashboard
 * Handles live dashboard updates and phase transitions.
 */
class ThermodynamicDashboard {
    constructor() {
        this.socket = null;
        this.refreshAll();
    }
    
    refreshAll() {
        this.loadPhaseDistribution();
        this.loadTransitions();
        this.loadSnowflakes();
    }
    
    async loadPhaseDistribution() {
        try {
            const response = await fetch('/api/v1/thermodynamics/phase-distribution');
            const data = await response.json();
            Object.entries(data).forEach(([phase, count]) => {
                const bar = document.querySelector(`.bar[data-phase="${phase}"] .count`);
                if (bar) bar.textContent = count;
            });
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
        } catch (e) {
            console.error("Failed to load phase distribution", e);
        }
    }
    
    async loadTransitions() {
        try {
            const response = await fetch('/api/v1/thermodynamics/transitions?limit=10');
            const data = await response.json();
            const feed = document.getElementById('transition-feed');
            feed.innerHTML = data.map(t => `
                <div class="transition-item">
                    <span>${t.icon} <strong>${t.description}</strong> - <em>${t.time}</em></span>
                </div>
            `).join('');
        } catch (e) {
            console.error("Failed to load transitions", e);
        }
    }
    
    async loadSnowflakes() {
        try {
            const response = await fetch('/api/v1/thermodynamics/snowflakes');
            const data = await response.json();
            const grid = document.getElementById('snowflake-grid');
            grid.innerHTML = data.map(s => `
                <div class="snowflake-card">
                    <h4>❄️ ${s.domain.charAt(0).toUpperCase() + s.domain.slice(1)}</h4>
                    <p>Patterns: ${s.patterns_count}</p>
                    <p>Confidence: ${(s.confidence * 100).toFixed(1)}%</p>
                    <button onclick="dashboard.branchSnowflake('${s.domain}')">Branch New</button>
                </div>
            `).join('');
        } catch (e) {
            console.error("Failed to load snowflakes", e);
        }
    }

    async branchSnowflake(domain) {
        const patternId = "p_base_001";
        try {
            const response = await fetch(`/api/v1/thermodynamics/snowflakes/${patternId}/branch/${domain}`, {
                method: 'POST'
            });
            const result = await response.json();
            alert(result.message);
            this.loadSnowflakes();
        } catch (e) {
            console.error("Failed to branch snowflake", e);
        }
    }
    
    initWebSocket() {
        const status = document.getElementById('system-state');
        status.textContent = "Connecting...";
        
        // WebSocket URL should be configured based on server environment
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/api/v1/thermodynamics/ws`;
        
        this.socket = new WebSocket(wsUrl);
        
        this.socket.onopen = () => {
            status.textContent = "Live";
            status.style.color = "green";
        };
        
        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'transition') {
                this.loadTransitions(); // Reload to get latest
            }
            if (data.type === 'distribution') {
                this.loadPhaseDistribution(); // Reload to get latest
            }
        };
        
        this.socket.onclose = () => {
            status.textContent = "Disconnected";
            status.style.color = "red";
        };
    }
}

// Global instance for UI callbacks
const dashboard = new ThermodynamicDashboard();
