import re

with open('app/api/v1/endpoints/dashboard/templates/base.html', 'r') as f:
    content = f.read()

# Find and fix the fetchPrimaryAIProvider function
old = '''async function fetchPrimaryAIProvider() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        console.log("DEBUG: Primary AI Provider:", data);
        
        // Update status on models tab
        const statusEl = document.getElementById('primary-ai-provider-status');
        if (statusEl) {
            statusEl.textContent = data.primary_provider || 'ollama';
            statusEl.className = 'tag tag-info';
        }
        
        // Update status on chat tab
        const statusChatEl = document.getElementById('primary-ai-provider-status-chat');
        if (statusChatEl) {
            statusChatEl.textContent = data.primary_provider || 'ollama';
            statusChatEl.className = 'tag tag-info';
        }
    } catch (e) {
        console.error('Error fetching primary AI provider:', e);
        ['primary-ai-provider-status', 'primary-ai-provider-status-chat'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = 'ollama';
                el.className = 'tag tag-info';
            }
        });
    }
}'''

new = '''async function fetchPrimaryAIProvider() {
    try {
        const res = await fetch('/api/v1/admin/dashboard/config/primary-ai-provider');
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        console.log("DEBUG: Primary AI Provider:", data);
        
        // Handle both string and object responses
        let providerName = data.primary_provider || data.provider || data.name || 'ollama';
        if (typeof providerName === 'object') {
            providerName = providerName.name || providerName.provider || 'ollama';
        }
        
        // Update status on models tab
        const statusEl = document.getElementById('primary-ai-provider-status');
        if (statusEl) {
            statusEl.textContent = providerName;
            statusEl.className = 'tag tag-info';
        }
        
        // Update status on chat tab
        const statusChatEl = document.getElementById('primary-ai-provider-status-chat');
        if (statusChatEl) {
            statusChatEl.textContent = providerName;
            statusChatEl.className = 'tag tag-info';
        }
    } catch (e) {
        console.error('Error fetching primary AI provider:', e);
        ['primary-ai-provider-status', 'primary-ai-provider-status-chat'].forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.textContent = 'ollama';
                el.className = 'tag tag-info';
            }
        });
    }
}'''

content = content.replace(old, new)

with open('app/api/v1/endpoints/dashboard/templates/base.html', 'w') as f:
    f.write(content)

print("✅ Fixed provider display")
