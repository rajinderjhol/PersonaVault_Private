
// ============ STREAMING CHAT ============

let streamingMessageId = null;
let eventSource = null;
let fullResponse = "";

async function sendChatMessageStream() {
    const input = document.getElementById("chat-input");
    if (!input) return;
    
    const query = input.value.trim();
    if (!query) return;
    
    console.log("📡 Sending streaming chat message:", query);
    
    // Clear previous thought process
    clearThoughtProcess();
    
    // Create session if none exists
    if (typeof currentSessionId === "undefined" || !currentSessionId) {
        if (typeof createNewSession === "function") {
            const newId = await createNewSession();
            if (!newId) {
                showToast("Please wait for session to create", "error");
                return;
            }
        }
    }
    
    const providerSelect = document.getElementById("chat-provider-select");
    const provider = providerSelect ? providerSelect.value : "ollama";
    
    // Add user message
    if (typeof addMessage === "function") addMessage("user", query);
    input.value = "";
    
    // Show thought process container
    const processContainer = document.getElementById("thought-process-container");
    if (processContainer) processContainer.style.display = "block";
    
    const stepsContainer = document.getElementById("thought-steps");
    if (stepsContainer) stepsContainer.style.display = "block";
    
    const label = document.getElementById("thought-toggle-label");
    if (label) label.textContent = "Hide";
    
    // Start timer
    if (typeof startThoughtTimer === "function") startThoughtTimer();
    
    // Show loading message
    if (typeof addMessage === "function") streamingMessageId = addMessage("ai", "...", true);
    
    try {
        const response = await fetch("/api/v1/chat/stream", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query: query,
                provider: provider,
                session_id: typeof currentSessionId !== "undefined" ? currentSessionId : null
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // Process SSE events
            const lines = buffer.split("\n\n");
            buffer = lines.pop() || "";
            
            for (const line of lines) {
                if (!line.trim()) continue;
                
                // Parse SSE event
                const eventMatch = line.match(/^event: (.+)$/m);
                const dataMatch = line.match(/^data: (.+)$/m);
                
                if (!dataMatch) continue;
                
                const eventType = eventMatch ? eventMatch[1] : "message";
                const data = JSON.parse(dataMatch[1]);
                
                handleStreamEvent(eventType, data);
            }
        }
    } catch (e) {
        console.error("Streaming error:", e);
        if (typeof hideTyping === "function") hideTyping();
        if (typeof stopThoughtTimer === "function") stopThoughtTimer();
        showToast("❌ Streaming error: " + e.message, "error");
    }
}

function handleStreamEvent(eventType, data) {
    console.log("📨 Stream event:", eventType, data);
    
    switch (eventType) {
        case "start":
            if (typeof showTyping === "function") showTyping();
            break;
            
        case "thought":
            if (typeof addThoughtStep === "function") {
                addThoughtStep({
                    step: data.step || 1,
                    label: data.label || "Processing",
                    description: data.description || "",
                    status: data.status || "complete",
                    duration: data.duration || 0
                });
            }
            break;
            
        case "content":
            fullResponse += data.content || "";
            updateStreamingMessage(fullResponse);
            break;
            
        case "trace":
            // Handle trace event by accessing data.trace directly
            console.log("Trace received:", data.trace);
            const msgEl = document.getElementById(streamingMessageId);
            if (msgEl) {
                // Add trace container to message
                const traceContainer = document.createElement('div');
                traceContainer.className = 'trace-container mt-2';
                traceContainer.innerHTML = `
                    <div class="text-xs text-gray-500 mb-1">🔍 Decision Trace:</div>
                    <div id="trace-${data.trace.id}" data-trace-viewer data-trace-id="${data.trace.id}"></div>
                `;
                msgEl.parentElement.appendChild(traceContainer);
                
                // Initialize trace viewer
                const viewer = new DecisionTraceViewer(`trace-${data.trace.id}`, data.trace.id, { isExpanded: false });
                viewer.render();
            }
            break;
            
        case "done":
            if (typeof stopThoughtTimer === "function") stopThoughtTimer();
            if (typeof hideTyping === "function") hideTyping();
            
            // finalResponse logic should probably move here or handle the trace data
            fullResponse = "";
            
            // If we have trace data, we need to update the streaming message container to include traces
            // This is complex, let's just re-render or append.
            if (typeof loadSessions === "function") loadSessions();
            break;
            
        case "error":
            if (typeof stopThoughtTimer === "function") stopThoughtTimer();
            if (typeof hideTyping === "function") hideTyping();
            updateStreamingMessage(`❌ Error: ${data.error || "Unknown error"}`);
            showToast("❌ Error: " + data.error, "error");
            fullResponse = "";
            break;
    }
}

function updateStreamingMessage(content) {
    const container = document.getElementById("chat-messages");
    if (!container) return;
    
    const msgEl = document.getElementById(streamingMessageId);
    if (msgEl) {
        msgEl.textContent = content;
        container.scrollTop = container.scrollHeight;
    }
}
