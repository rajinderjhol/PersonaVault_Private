/**
 * Swarm Status - Real-time agent swarm visualization
 */
class SwarmStatus {
    constructor() {
        this.websocket = null;
        this.agents = {};
        this.updateInterval = null;
        this.isConnected = false;
    }

    init() {
        this.container = document.getElementById('swarm-status-container');
        if (!this.container) return;
        this.render();
        this.connectWebSocket();
        this.startPolling();
    }
    
    render() {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="swarm-status-panel">
                <div class="swarm-header">
                    <span class="icon">🐝</span>
                    <span class="title">Agent Swarm</span>
                    <span class="status-badge" id="swarm-status-badge">● Connected</span>
                    <span class="agent-count" id="agent-count">0 agents</span>
                </div>
                
                <div class="swarm-visualization" id="swarm-visualization">
                    <div class="swarm-grid" id="swarm-grid">
                        <!-- Agents rendered here -->
                    </div>
                </div>
                
                <div class="swarm-activity" id="swarm-activity">
                    <div class="activity-header">
                        <span>📊 Activity</span>
                        <span id="active-count">0 active</span>
                    </div>
                    <div class="collaboration-pipeline" id="collaboration-pipeline">
                        <!-- Pipeline visualization -->
                    </div>
                </div>
            </div>
        `;
    }
    
    connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/api/v1/swarm/ws`;
        
        this.websocket = new WebSocket(wsUrl);
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            this.updateBadge('connected');
        };
        
        this.websocket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'swarm_status') {
                this.updateStatus(data.data);
            }
        };
        
        this.websocket.onclose = () => {
            this.isConnected = false;
            this.updateBadge('disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };
    }
    
    startPolling() {
        // Fallback polling if WebSocket fails
        this.updateInterval = setInterval(async () => {
            if (!this.isConnected) {
                try {
                    const response = await fetch('/api/v1/swarm/status');
                    const status = await response.json();
                    this.updateStatus(status);
                } catch (error) {
                    console.warn('Swarm status polling failed:', error);
                }
            }
        }, 3000);
    }
    
    updateStatus(status) {
        this.agents = status;
        this.renderAgents(status);
        this.renderActivity(status);
        this.updateCounts(status);
    }
    
    renderAgents(status) {
        const grid = document.getElementById('swarm-grid');
        if (!grid) return;
        
        const activeAgents = status.active_agents || [];
        const idleAgents = status.idle_agents || [];
        const allAgents = [...activeAgents, ...idleAgents.map(name => ({ name, status: 'idle' }))];
        
        grid.innerHTML = allAgents.map(agent => {
            const isActive = activeAgents.some(a => a.name === agent.name);
            const agentData = activeAgents.find(a => a.name === agent.name);
            
            return `
                <div class="swarm-agent ${isActive ? 'active' : 'idle'}">
                    <div class="agent-icon">${this.getAgentIcon(agent.name)}</div>
                    <div class="agent-info">
                        <span class="agent-name">${this.formatAgentName(agent.name)}</span>
                        <span class="agent-status">${isActive ? '● Active' : '○ Idle'}</span>
                        ${isActive ? `<span class="agent-task">${agentData.task || 'Processing'}</span>` : ''}
                        ${isActive ? `<span class="agent-provider">${agentData.provider || 'local'}</span>` : ''}
                    </div>
                    ${isActive ? `
                        <div class="agent-confidence">
                            <span class="confidence-bar" style="width: ${(agentData.confidence || 0.5) * 100}%"></span>
                            <span class="confidence-label">${Math.round((agentData.confidence || 0.5) * 100)}%</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
        
        // Animate active agents
        this.animateSwarm();
    }
    
    renderActivity(status) {
        const pipeline = document.getElementById('collaboration-pipeline');
        if (!pipeline) return;
        
        const collaboration = status.collaboration || {};
        const pipelineAgents = collaboration.pipeline || [];
        const currentStep = collaboration.current_step;
        
        if (pipelineAgents.length === 0) {
            pipeline.innerHTML = `
                <div class="pipeline-empty">
                    <span>🤝 No active collaboration</span>
                    <span class="sub">Agents are idle, waiting for tasks</span>
                </div>
            `;
            return;
        }
        
        pipeline.innerHTML = `
            <div class="pipeline-flow">
                ${pipelineAgents.map((agent, index) => {
                    const isActive = agent === currentStep;
                    const isCompleted = index < pipelineAgents.indexOf(currentStep);
                    return `
                        <div class="pipeline-step ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}">
                            <span class="step-icon">${isActive ? '🔄' : (isCompleted ? '✅' : '○')}</span>
                            <span class="step-name">${this.formatAgentName(agent)}</span>
                            ${isActive ? '<span class="step-label">Processing</span>' : ''}
                            ${isCompleted ? '<span class="step-label">Done</span>' : ''}
                        </div>
                        ${index < pipelineAgents.length - 1 ? '<span class="pipeline-arrow">→</span>' : ''}
                    `;
                }).join('')}
            </div>
            <div class="pipeline-status">
                ${collaboration.active ? '🔄 Swarm actively processing' : '💤 Swarm idle'}
            </div>
        `;
    }
    
    updateCounts(status) {
        const count = document.getElementById('agent-count');
        const activeCount = document.getElementById('active-count');
        
        if (count) {
            const total = status.total_agents || 0;
            count.textContent = `${total} agents`;
        }
        
        if (activeCount) {
            const active = status.active_count || 0;
            activeCount.textContent = `${active} active`;
        }
    }
    
    updateBadge(state) {
        const badge = document.getElementById('swarm-status-badge');
        if (!badge) return;
        
        if (state === 'connected') {
            badge.textContent = '● Connected';
            badge.className = 'status-badge connected';
        } else {
            badge.textContent = '○ Disconnected';
            badge.className = 'status-badge disconnected';
        }
    }
    
    animateSwarm() {
        // Add pulse animation to active agents
        document.querySelectorAll('.swarm-agent.active').forEach((el, index) => {
            el.style.animationDelay = `${index * 0.2}s`;
        });
    }
    
    getAgentIcon(agentName) {
        const icons = {
            'GeneratorAgent': '🧠',
            'RetrievalAgent': '🔍',
            'ValidatorAgent': '✅',
            'SecurityAgent': '🔒',
            'ComplianceAgent': '📋',
            'ClinicalReasoningAgent': '🏥',
            'ClinicalValidatorAgent': '⚕️'
        };
        return icons[agentName] || '🤖';
    }
    
    formatAgentName(agentName) {
        // Convert CamelCase to readable format
        return agentName.replace(/([A-Z])/g, ' $1').trim();
    }
}

// Initialize
const status = new SwarmStatus();
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    status.init();
} else {
    document.addEventListener('DOMContentLoaded', () => {
        status.init();
    });
}
window.swarmStatus = status;
