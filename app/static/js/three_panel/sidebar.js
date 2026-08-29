/**
 * Sidebar Customization - Manage user sidebar elements
 */

class SidebarManager {
    constructor() {
        this.prefs = null;
        this.dragging = null;
    }

    async init() {
        console.log("SidebarManager: initializing...");
        await this.loadPrefs();
        this.renderElements();
        console.log("SidebarManager: initialized.");
    }

    async loadPrefs() {
        console.log("SidebarManager: loading prefs...");
        try {
            const response = await fetch('/api/v1/user/preferences/sidebar');
            console.log("SidebarManager: prefs response status:", response.status);
            if (response.ok) {
                this.prefs = await response.json();
                console.log("SidebarManager: prefs loaded:", this.prefs);
            } else {
                console.warn('SidebarManager: API failed, using default sidebar preferences');
                this.prefs = this.getDefaultPrefs();
            }
        } catch (error) {
            console.warn('SidebarManager: Failed to load sidebar prefs, using defaults:', error);
            this.prefs = this.getDefaultPrefs();
        }
        this.renderElements();
    }

    getDefaultPrefs() {
        return {
            elements: [
                { id: 'dashboard', type: 'navigation', label: 'Dashboard', icon: '📊' },
                { id: 'chat', type: 'navigation', label: 'Chat', icon: '💬' },
                { id: 'swarm', type: 'navigation', label: 'Swarm', icon: '🐝' }
            ],
            order: ['dashboard', 'chat', 'swarm'],
            collapsed: false
        };
    }

    renderElements() {
        const container = document.getElementById('sidebar-nav');
        if (!container) {
            console.error("SidebarManager: sidebar-nav not found");
            return;
        }

        const ordered = this.prefs.order
            .map(id => this.prefs.elements.find(e => e.id === id))
            .filter(e => e && e.visible !== false);

        container.innerHTML = ordered.map(el => `
            <div class="sidebar-item ${el.type}" data-id="${el.id}" onclick="console.log('Sidebar clicked: ${el.id}'); loadTab('${el.id}')">
                <span class="icon">${el.icon || '📄'}</span>
                <span class="label">${el.label}</span>
            </div>
        `).join('');
        console.log("SidebarManager: rendered elements:", ordered.length);
    }

    async addElement(type, label) {
        const id = `${type}-${label.toLowerCase().replace(/\s+/g, '-')}`;
        const element = { id, type, label, icon: this.getIcon(type, label) };
        
        try {
            const response = await fetch('/api/v1/user/preferences/sidebar/elements', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(element)
            });
            if (response.ok) {
                this.prefs.elements.push(element);
                this.prefs.order.push(id);
                this.renderElements();
            } else {
                console.warn('SidebarManager: API failed, adding element locally');
                this.prefs.elements.push(element);
                this.prefs.order.push(id);
                this.renderElements();
            }
        } catch (error) {
            console.warn('SidebarManager: Network error, adding element locally:', error);
            this.prefs.elements.push(element);
            this.prefs.order.push(id);
            this.renderElements();
        }
    }

    getIcon(type, label) {
        const icons = {
            'Security': '🔒',
            'Compliance': '⚖️',
            'Contract': '📄',
            'Procurement': '📦',
            'Robotics': '🤖',
            'Snowflakes': '❄️',
            'Metrics': '📊',
            'Pattern': '📌'
        };
        return icons[label] || '📄';
    }
}

// Global instance
const sidebarManager = new SidebarManager();
document.addEventListener('DOMContentLoaded', () => sidebarManager.init());

function closeSidebarEditor() {
    document.getElementById('sidebar-editor').style.display = 'none';
}
