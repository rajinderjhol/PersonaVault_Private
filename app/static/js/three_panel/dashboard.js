/**
 * Dashboard - Core three-panel functionality
 */

// Toggle sidebar collapse
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
    }
}

// Toggle context panel (right sidebar)
function toggleContextPanel() {
    const contextPanel = document.querySelector('.context-panel');
    if (contextPanel) {
        contextPanel.classList.toggle('collapsed');
    }
}

// Load tab content
async function loadTab(tabId) {
    if (tabId === 'chat') return; // Chat is loaded by default
    
    const container = document.querySelector('.chat-container');
    if (!container) return;

    container.innerHTML = '<div class="loading">Loading...</div>';
    
    try {
        const response = await fetch(`/api/v1/admin/dashboard/tab/${tabId}`);
        if (response.ok) {
            container.innerHTML = await response.text();
        } else {
            container.innerHTML = `<div class="error">Failed to load tab: ${tabId}</div>`;
        }
    } catch (e) {
        container.innerHTML = `<div class="error">Error: ${e.message}</div>`;
    }
}

// Close sidebar editor
function closeSidebarEditor() {
    const editor = document.getElementById('sidebar-editor');
    if (editor) {
        editor.style.display = 'none';
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('🛡️ Three-Panel Dashboard initialized.');
    
    // Make sidebar not collapsed by default
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.remove('collapsed');
    }

    // Load tab if provided in URL
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    if (tab) {
        loadTab(tab);
    }
});