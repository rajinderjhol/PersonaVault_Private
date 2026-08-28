/**
 * Integrations - Connect and manage external services
 */

class IntegrationsPanel {
    constructor() {
        this.integrations = [];
        this.connected = [];
        this.isLoading = false;
    }
    
    init() {
        this.container = document.getElementById('integrations-container');
        if (!this.container) return;
        this.loadIntegrations();
    }
    
    async loadIntegrations() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        try {
            const response = await fetch('/api/v1/integrations/');
            const data = await response.json();
            this.integrations = data.integrations || [];
            this.connected = data.connected || [];
            this.render();
        } catch (error) {
            console.error('Failed to load integrations:', error);
        }
        
        this.isLoading = false;
    }
    
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="integrations-panel">
                <div class="integrations-header">
                    <div class="header-left">
                        <span class="icon">🔌</span>
                        <span class="title">Integrations</span>
                        <span class="badge">${this.connected.length} connected</span>
                    </div>
                </div>
                <div class="integrations-grid">
                    ${this.integrations.map(integration => {
                        const isConnected = this.connected.some(c => c.id === integration.id);
                        return `
                            <div class="integration-card ${isConnected ? 'connected' : 'available'}">
                                <div class="integration-icon">${integration.icon || '🔌'}</div>
                                <div class="integration-info">
                                    <span class="integration-name">${integration.name}</span>
                                </div>
                                <div class="integration-status">
                                    <span class="status-badge ${isConnected ? 'connected' : 'available'}">
                                        ${isConnected ? '✅ Connected' : 'Available'}
                                    </span>
                                </div>
                                <div class="integration-actions">
                                    <button class="action-btn ${isConnected ? 'secondary' : 'primary'}" onclick="integrationsPanel.connect('${integration.id}')">
                                        ${isConnected ? 'Reconfigure' : 'Connect'}
                                    </button>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }
    
    async connect(integrationId) {
        // Simple demo connection flow
        const key = prompt(`Enter API key for integration:`);
        if (!key) return;
        
        try {
            await fetch(`/api/v1/integrations/${integrationId}/connect`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    type: 'api_key',
                    credentials: { api_key: key }
                })
            });
            await this.loadIntegrations();
        } catch (error) {
            console.error('Failed to connect:', error);
        }
    }
}

// Initialize
window.integrationsPanel = new IntegrationsPanel();
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    window.integrationsPanel.init();
} else {
    document.addEventListener('DOMContentLoaded', () => {
        window.integrationsPanel.init();
    });
}
