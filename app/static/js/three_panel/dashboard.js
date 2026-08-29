/**
 * Dashboard Controller
 */
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
    }
    const wrapper = document.querySelector('.dashboard-wrapper');
    if (wrapper) {
        wrapper.classList.toggle('sidebar-collapsed');
    }
}

function closeSidebarEditor() {
    const editor = document.getElementById('sidebar-editor');
    if (editor) {
        editor.style.display = 'none';
    }
}

async function loadTab(tabId) {
    console.log("loadTab called with tabId:", tabId);
    const container = document.querySelector('.chat-container');
    if (!container) {
        console.error("Chat container not found!");
        return;
    }
    
    // If the tab is 'chat', we might want to reload the chat container differently
    if (tabId === 'chat') {
        window.location.reload(); // Simple reload to get back to chat
        return;
    }

    try {
        console.log("Fetching tab from:", `/api/v1/admin/dashboard/tab/${tabId}`);
        const response = await fetch(`/api/v1/admin/dashboard/tab/${tabId}`, {
            credentials: 'include'
        });
        console.log("Tab response status:", response.status);
        if (response.ok) {
            container.innerHTML = await response.text();
        } else {
            container.innerHTML = `<div class="card">Error loading tab: ${tabId} (Status: ${response.status})</div>`;
        }
    } catch (error) {
        console.error('Failed to load tab:', error);
    }
}

console.log("Three-Panel Dashboard initialized.");
