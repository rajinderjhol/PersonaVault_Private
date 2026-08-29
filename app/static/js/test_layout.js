/**
 * Layout Verification Test Suite
 */

async function runLayoutTests() {
    const results = document.getElementById('test-results');
    results.innerHTML = '<h3>Running Tests...</h3>';
    
    const log = (msg, success = true) => {
        results.innerHTML += `<p style="color: ${success ? 'green' : 'red'}">${success ? '✅' : '❌'} ${msg}</p>`;
    };
    
    try {
        // 1. Verify LayoutManager exists
        if (!window.layoutManager) throw new Error("LayoutManager not initialized");
        log("LayoutManager initialized");
        
        // 2. Test Sidebar Toggle
        const container = document.querySelector('.chat-premium');
        window.layoutManager.toggleSidebar();
        if (container.classList.contains('sidebar-collapsed')) {
            log("Sidebar collapsed successfully");
        } else {
            throw new Error("Sidebar did not collapse");
        }
        window.layoutManager.toggleSidebar(); // Reset
        
        // 3. Test Panel Toggle
        window.layoutManager.togglePanel();
        if (container.classList.contains('panel-collapsed')) {
            log("Intelligence panel collapsed successfully");
        } else {
            throw new Error("Intelligence panel did not collapse");
        }
        window.layoutManager.togglePanel(); // Reset
        
        // 4. Test LocalStorage Persistence
        const state = JSON.parse(localStorage.getItem('personavault_layout'));
        if (state) log("Layout state persisted to localStorage");
        else throw new Error("Layout state not persisted");
        
        log("ALL TESTS PASSED");
    } catch (e) {
        log(e.message, false);
    }
}

document.addEventListener('DOMContentLoaded', runLayoutTests);
