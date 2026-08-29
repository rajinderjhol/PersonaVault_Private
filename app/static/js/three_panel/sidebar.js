/**
 * Sidebar Manager - Navigation and customization
 */

class SidebarManager {
    constructor() {
        this.elements = [];
        this.init();
    }

    init() {
        console.log('SidebarManager: initializing...');
        this.loadElements();
        this.renderElements();
        console.log('SidebarManager: initialized.');
    }

    loadElements() {
        // Expanded navigation elements including v1 tabs
        this.elements = [
            { id: 'dashboard', icon: '📊', label: 'Dashboard', url: '/api/v1/admin/dashboard/v2' },
            { id: 'chat', icon: '💬', label: 'Chat', url: '/api/v1/admin/dashboard/v2?tab=chat' },
            { id: 'swarm', icon: '🐝', label: 'Swarm', url: '/api/v1/admin/dashboard/v2?tab=swarm' },
            { id: 'compliance', icon: '⚖️', label: 'Compliance', url: '/api/v1/admin/dashboard/v2?tab=governance' },
            { id: 'security', icon: '🔒', label: 'Security', url: '/api/v1/admin/dashboard/v2?tab=security' },
            { id: 'agents', icon: '🤖', label: 'Agents', url: '/api/v1/admin/dashboard/v2?tab=agents' },
            { id: 'models', icon: '🧠', label: 'Models', url: '/api/v1/admin/dashboard/v2?tab=models' },
            { id: 'overview', icon: '📈', label: 'Overview', url: '/api/v1/admin/dashboard/v2?tab=overview' }
        ];
    }

    renderElements() {
        const container = document.getElementById('sidebar-nav');
        if (!container) return;

        container.innerHTML = this.elements.map(el => `
            <a href="${el.url}" class="nav-item" data-id="${el.id}">
                <span class="nav-icon">${el.icon}</span>
                <span class="nav-label">${el.label}</span>
            </a>
        `).join('');

        // Mark active based on current URL
        const currentPath = window.location.pathname;
        container.querySelectorAll('.nav-item').forEach(item => {
            if (currentPath.includes(item.getAttribute('href').split('?')[0])) {
                item.classList.add('active');
            }
        });
    }

    addElement(type, label) {
        const icons = {
            'Security': '🔒',
            'Compliance': '⚖️',
            'Contract': '📄',
            'Procurement': '📦'
        };
        const icon = icons[label] || '📌';
        const id = `${type}-${label.toLowerCase()}`;
        
        this.elements.push({ id, icon, label, url: '#' });
        this.renderElements();
        
        // Close the modal
        closeSidebarEditor();
    }
}

// Initialize sidebar manager
document.addEventListener('DOMContentLoaded', function() {
    window.sidebarManager = new SidebarManager();
});