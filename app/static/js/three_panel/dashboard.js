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
});