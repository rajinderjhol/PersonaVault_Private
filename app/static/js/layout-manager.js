/**
 * Three-Column Sovereign Workbench Layout Manager
 */

class LayoutManager {
    constructor() {
        this.sidebarCollapsed = false;
        this.panelCollapsed = false;
        this.tabs = this.getDefaultTabs();
        this.loadSavedState();
        this.init();
    }
    
    getDefaultTabs() {
        return [
            { id: 'new-chat', icon: '➕', label: 'New Chat', visible: true, order: 0 },
            { id: 'history', icon: '🕒', label: 'History', visible: true, order: 1 },
            { id: 'packs', icon: '📦', label: 'My Packs', visible: true, order: 2 },
            { id: 'integrations', icon: '🔌', label: 'Integrations', visible: true, order: 3 },
            { id: 'patterns', icon: '💎', label: 'Patterns', visible: false, order: 4 },
            { id: 'analytics', icon: '📊', label: 'Analytics', visible: false, order: 5 },
            { id: 'profile', icon: '👤', label: 'Profile', visible: true, order: 6 }
        ];
    }
    
    loadSavedState() {
        try {
            const saved = localStorage.getItem('personavault_layout');
            if (saved) {
                const data = JSON.parse(saved);
                this.tabs = data.tabs || this.tabs;
                this.sidebarCollapsed = data.sidebarCollapsed || false;
                this.panelCollapsed = data.panelCollapsed || false;
            }
        } catch (e) {
            console.debug('No saved layout state');
        }
    }
    
    saveState() {
        try {
            localStorage.setItem('personavault_layout', JSON.stringify({
                tabs: this.tabs,
                sidebarCollapsed: this.sidebarCollapsed,
                panelCollapsed: this.panelCollapsed
            }));
        } catch (e) {
            console.debug('Failed to save layout state');
        }
    }
    
    init() {
        this.renderSidebar();
        this.renderIntelligencePanel();
        this.setupCollapseToggles();
        this.setupDragAndDrop();
    }
    
    renderSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;
        
        const visibleTabs = this.tabs
            .filter(t => t.visible)
            .sort((a, b) => a.order - b.order);
        
        // Update nav items
        const nav = sidebar.querySelector('.sidebar-nav');
        if (nav) {
            nav.innerHTML = `
                <div class="nav-section">
                    <div class="section-title">Navigation</div>
                    ${visibleTabs.map(tab => `
                        <div class="nav-item" data-tab="${tab.id}" draggable="true">
                            <span class="icon">${tab.icon}</span>
                            <span>${tab.label}</span>
                            <span class="drag-handle">⠿</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }
    
    renderIntelligencePanel() {
        const panel = document.querySelector('.intelligence-panel');
        if (!panel) return;
        
        panel.innerHTML = `
            <div class="panel-header">
                <span class="title">🧠 Intelligence</span>
                <button class="toggle-btn" onclick="layoutManager.togglePanel()">◀</button>
            </div>
            
            <div id="suggestions-container" class="panel-section">
                <!-- Proactive suggestions will be injected here -->
            </div>
            
            <div class="panel-section">
                <div class="section-title">🏷️ Domain</div>
                <div class="domain-controls">
                    <div class="current-domain">
                        <span>Legal</span>
                        <span style="font-size:12px;color:var(--text-muted)">· 92%</span>
                    </div>
                    <div class="domain-actions">
                        <button class="domain-btn active">Legal</button>
                        <button class="domain-btn">Security</button>
                        <button class="domain-btn">Compliance</button>
                        <button class="domain-btn">Clinical</button>
                    </div>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="section-title">🧊 Memory Lineage</div>
                <div class="memory-lineage">
                    <div class="memory-layer-item">
                        <span class="layer-icon">💨</span>
                        <span class="layer-name">Gas</span>
                        <span class="layer-count">12 tokens</span>
                        <div class="layer-bar"><div class="fill gas" style="width:30%"></div></div>
                    </div>
                    <div class="memory-layer-item">
                        <span class="layer-icon">💧</span>
                        <span class="layer-name">Liquid</span>
                        <span class="layer-count">23 episodes</span>
                        <div class="layer-bar"><div class="fill liquid" style="width:60%"></div></div>
                    </div>
                    <div class="memory-layer-item">
                        <span class="layer-icon">🧊</span>
                        <span class="layer-name">Ice</span>
                        <span class="layer-count">47 patterns</span>
                        <div class="layer-bar"><div class="fill ice" style="width:90%"></div></div>
                    </div>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="section-title">🐝 Active Agents</div>
                <div class="agent-status">
                    <span class="agent-chip"><span class="status-dot active"></span> Generator</span>
                    <span class="agent-chip"><span class="status-dot active"></span> Retrieval</span>
                    <span class="agent-chip"><span class="status-dot idle"></span> Validator</span>
                    <span class="agent-chip"><span class="status-dot idle"></span> Security</span>
                </div>
            </div>
            
            <div class="panel-section">
                <div class="section-title">🔗 Citations</div>
                <div style="font-size:13px;color:var(--text-muted);padding:8px;">
                    No citations yet. Ask a question to see sources.
                </div>
            </div>
        `;
    }
    
    setupCollapseToggles() {
        const sidebar = document.querySelector('.sidebar');
        const panel = document.querySelector('.intelligence-panel');
        
        // Sidebar collapse
        const sidebarToggle = sidebar?.querySelector('.toggle-btn');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }
        
        // Panel collapse
        const panelToggle = panel?.querySelector('.toggle-btn');
        if (panelToggle) {
            panelToggle.addEventListener('click', () => this.togglePanel());
        }
    }
    
    toggleSidebar() {
        this.sidebarCollapsed = !this.sidebarCollapsed;
        const container = document.querySelector('.chat-premium');
        container.classList.toggle('sidebar-collapsed', this.sidebarCollapsed);
        this.saveState();
    }
    
    togglePanel() {
        this.panelCollapsed = !this.panelCollapsed;
        const container = document.querySelector('.chat-premium');
        container.classList.toggle('panel-collapsed', this.panelCollapsed);
        this.saveState();
    }
    
    setupDragAndDrop() {
        // Drag-and-drop for tab reordering
        const items = document.querySelectorAll('.nav-item[draggable]');
        let dragItem = null;
        
        items.forEach(item => {
            item.addEventListener('dragstart', (e) => {
                dragItem = item;
                item.classList.add('dragging');
            });
            
            item.addEventListener('dragend', () => {
                item.classList.remove('dragging');
            });
            
            item.addEventListener('dragover', (e) => {
                e.preventDefault();
                const rect = item.getBoundingClientRect();
                const midY = rect.top + rect.height / 2;
                
                if (e.clientY > midY) {
                    item.parentNode.insertBefore(dragItem, item.nextSibling);
                } else {
                    item.parentNode.insertBefore(dragItem, item);
                }
            });
        });
    }
    
    showTabCustomizer() {
        // Modal for customizing sidebar tabs
        const modal = document.createElement('div');
        modal.className = 'tab-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <span class="title">⚙️ Customize Sidebar</span>
                    <button class="close-btn" onclick="this.closest('.tab-modal').remove()">×</button>
                </div>
                ${this.tabs.map(tab => `
                    <div class="tab-item">
                        <span>${tab.icon}</span>
                        <span>${tab.label}</span>
                        <div class="toggle ${tab.visible ? 'active' : ''}" 
                             onclick="layoutManager.toggleTabVisibility('${tab.id}')">
                            <div class="knob"></div>
                        </div>
                    </div>
                `).join('')}
                <button onclick="this.closest('.tab-modal').remove()" 
                        style="width:100%;padding:12px;border:none;border-radius:8px;background:var(--color-primary);color:white;font-weight:600;cursor:pointer;">
                    Done
                </button>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    toggleTabVisibility(tabId) {
        const tab = this.tabs.find(t => t.id === tabId);
        if (tab) {
            tab.visible = !tab.visible;
            this.saveState();
            this.renderSidebar();
        }
    }
}

// Initialize layout manager
document.addEventListener('DOMContentLoaded', () => {
    window.layoutManager = new LayoutManager();
});
