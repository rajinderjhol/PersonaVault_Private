"""
UI Template for the PersonaVault Admin Dashboard.
Separated from logic to prevent monolithic code growth.
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PersonaVault Admin</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root { --accent: #38bdf8; --bg: #0f172a; --card-bg: #1e293b; --sidebar: #111827; --border: #334155; --success: #34d399; --warning: #fbbf24; --danger: #f87171; }
        * { box-sizing: border-box; }
        body { font-family: 'Inter', -apple-system, sans-serif; background: var(--bg); color: #f1f5f9; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: var(--card-bg); display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding: 15px 30px; z-index: 10; flex-shrink: 0; }
        h1 { color: #38bdf8; margin: 0; font-size: 22px; font-weight: 800; letter-spacing: -0.025em; }
        .layout { display: flex; flex: 1; overflow: hidden; }
        .sidebar { width: 260px; background: var(--sidebar); border-right: 1px solid var(--border); display: flex; flex-direction: column; padding-top: 20px; overflow-y: auto; flex-shrink: 0; }
        .nav-group { margin-bottom: 25px; }
        .nav-label { padding: 0 30px; font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 10px; }
        .nav-item { padding: 12px 30px; cursor: pointer; color: #94a3b8; font-size: 14px; transition: all 0.2s; border-left: 3px solid transparent; display: flex; align-items: center; gap: 10px; }
        .nav-item:hover { background: rgba(56, 189, 248, 0.05); color: #f1f5f9; }
        .nav-item.active { background: rgba(56, 189, 248, 0.1); color: var(--accent); border-left-color: var(--accent); font-weight: 600; }
        .main-content { flex: 1; overflow-y: auto; padding: 40px; }
        .tab-content { display: none; animation: fadeIn 0.3s ease-out; }
        .tab-content.active { display: block; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 25px; margin-bottom: 40px; }
        .card { background: var(--card-bg); border-radius: 12px; padding: 25px; border: 1px solid var(--border); transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
        .card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2); }
        .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .card-title { font-size: 14px; font-weight: 700; color: var(--accent); text-transform: uppercase; margin: 0; }
        .metric-value { font-size: 36px; font-weight: 800; color: #fbbf24; margin: 10px 0; }
        .metric-label { color: #94a3b8; text-transform: uppercase; font-size: 12px; font-weight: 600; letter-spacing: 0.05em; }
        .tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; background: var(--border); color: #f1f5f9; }
        .tag-success { background: #065f46; color: #34d399; }
        .btn { display: inline-flex; align-items: center; gap: 8px; background: var(--accent); color: #0f172a; padding: 10px 20px; border-radius: 6px; text-decoration: none; font-weight: 700; border: none; cursor: pointer; transition: all 0.2s; }
        .btn:hover { background: #7dd3fc; }
        .refresh-btn { cursor: pointer; color: var(--accent); background: transparent; border: 1px solid var(--accent); padding: 8px 16px; border-radius: 6px; font-weight: 600; transition: all 0.2s; }
        .refresh-btn:hover { background: rgba(56, 189, 248, 0.1); }
        pre { background: #020617; padding: 20px; border-radius: 8px; color: var(--accent); border: 1px solid var(--border); line-height: 1.5; white-space: pre-wrap; word-break: break-all; font-size: 13px; max-height: 400px; overflow: auto; }
        .input-field { width: 100%; padding: 10px; margin: 10px 0; border-radius: 4px; border: 1px solid #334155; background: #020617; color: white; box-sizing: border-box; }
        .mem-viz-container { margin-top: 15px; background: #020617; border-radius: 6px; height: 14px; display: flex; overflow: hidden; border: 1px solid var(--border); }
        .viz-l2 { background: #38bdf8; height: 100%; transition: width 0.6s ease-in-out; }
        .viz-l3 { background: #a855f7; height: 100%; transition: width 0.6s ease-in-out; }
        .viz-legend { display: flex; gap: 20px; margin-top: 10px; font-size: 11px; color: #94a3b8; }
        .log-container { background: #020617; flex-grow: 1; overflow-y: auto; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 11px; border: 1px solid var(--border); white-space: pre-wrap; line-height: 1.4; max-height: 500px; }
        .log-line-error { color: #f87171; }
        .log-line-warning { color: #fbbf24; }
        .log-line-info { color: #38bdf8; }
        .flex-between { display: flex; justify-content: space-between; align-items: center; }
        .stat-row { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
        .stat-row:last-child { border-bottom: none; }
        .stat-label { color: #94a3b8; }
        .stat-value { color: #f1f5f9; font-weight: 600; font-family: monospace; }
        .toast-container { position: fixed; bottom: 30px; right: 30px; z-index: 1000; display: flex; flex-direction: column; gap: 12px; }
        .toast { background: var(--card-bg); border: 1px solid var(--border); border-left: 4px solid var(--accent); padding: 14px 24px; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3); min-width: 280px; animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1); display: flex; align-items: center; gap: 12px; transition: all 0.3s; }
        @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        .toast.success { border-left-color: var(--success); }
        .toast.error { border-left-color: var(--danger); }
        .toast.info { border-left-color: var(--accent); }
        .modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.85); backdrop-filter: blur(4px); }
        .modal-content { background: var(--card-bg); margin: 5% auto; padding: 30px; border: 1px solid var(--border); width: 85%; max-width: 900px; border-radius: 12px; position: relative; max-height: 85vh; overflow-y: auto; }
        .close-modal { position: absolute; top: 20px; right: 25px; color: #64748b; font-size: 28px; cursor: pointer; }
        .close-modal:hover { color: white; }
    </style>
</head>
<body>
    <header>
        <h1>🛡️ PersonaVault System Control</h1>
        <div style="display: flex; gap: 10px;">
            <button class="refresh-btn" onclick="fetchMetrics()"><i class="fas fa-sync-alt"></i> Refresh</button>
            <button class="refresh-btn" style="color: var(--danger); border-color: var(--danger);" onclick="logout()"><i class="fas fa-sign-out-alt"></i> Logout</button>
        </div>
    </header>
    
    <div class="layout">
        <nav class="sidebar">
            <div class="nav-group">
                <div class="nav-label">Core Pulse</div>
                <div class="nav-item active" onclick="switchTab(event, 'overview')">📊 System Overview</div>
                <div class="nav-item" onclick="switchTab(event, 'models')">📦 Model Management</div>
                <div class="nav-item" onclick="switchTab(event, 'logs')">📜 System Logs</div>
            </div>
            <div class="nav-group">
                <div class="nav-label">Cognitive Architecture</div>
                <div class="nav-item" onclick="switchTab(event, 'lattices')">🕸️ Memory Lattices</div>
                <div class="nav-item" onclick="switchTab(event, 'learning')">⚡ Graduation Logic</div>
                <div class="nav-item" onclick="switchTab(event, 'agents')">🤖 Agent Orchestration</div>
                <div class="nav-item" onclick="switchTab(event, 'mcp')">🔌 MCP Registry</div>
            </div>
            <div class="nav-group">
                <div class="nav-label">Enterprise & Safety</div>
                <div class="nav-item" onclick="switchTab(event, 'governance')">⚖️ Governance & Audit</div>
                <div class="nav-item" onclick="switchTab(event, 'security')">🔐 Privacy Vault</div>
            </div>
        </nav>
        
        <main class="main-content">
            <div id="overview-tab" class="tab-content active">
                <div id="metrics-grid" class="grid">
                    <div class="card"><div class="metric-label">Loading...</div></div>
                </div>
                <div class="card" style="margin-bottom: 25px; border-top: 4px solid #fbbf24;">
                    <h3 class="card-title">Laboratory & Simulation</h3>
                    <p style="color: #94a3b8; font-size: 13px;">Trigger virtual telemetry to test real-time monitoring and HITL triggers.</p>
                    <button class="btn" id="sim-btn" onclick="toggleSimulation()"><i class="fas fa-bolt"></i> Ignite IoT Simulation</button>
                </div>
                <h2 style="margin-top: 40px; color: #94a3b8; font-size: 14px; text-transform: uppercase;">Raw Intelligence Feed</h2>
                <pre id="raw-metrics">Fetching system state...</pre>
            </div>

            <div id="models-tab" class="tab-content">
                <h2 style="color: var(--accent);">AI Model Management (Ollama)</h2>
                <div class="card" style="margin-bottom: 25px;">
                    <h3 style="margin-top:0; color: #38bdf8;">Pull New Model</h3>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="new-model-input" placeholder="e.g. llama3" class="input-field" style="flex:1;">
                        <button class="btn" onclick="triggerModelPull()"><i class="fas fa-download"></i> Pull Model</button>
                    </div>
                    <div id="pull-status" style="margin-top: 15px; font-family: monospace; font-size: 11px; color: #fbbf24; white-space: pre-wrap;"></div>
                </div>
                <div class="card">
                    <h3 style="margin-top:0; color: #34d399;">Installed Local Models</h3>
                    <div id="models-list" style="display: flex; flex-direction: column; gap: 12px;">
                        <div class="metric-label">Loading models...</div>
                    </div>
                </div>
            </div>

            <div id="lattices-tab" class="tab-content">
                <h2 style="color: var(--accent);">Memory Lattices (Layers 1-3)</h2>
                <p style="color: #94a3b8; font-size: 14px; margin-bottom: 20px;">
                    Visualization of the conversion from Volatile Context (Gas) to Episodic Memory (Liquid) and Semantic Constraints (Ice).
                </p>
                <div class="card" style="margin-bottom: 25px; border-left: 4px solid #a855f7;">
                    <div class="metric-label">Memory Distribution Ratio</div>
                    <div class="mem-viz-container">
                        <div id="bar-l2" class="viz-l2" style="width: 50%"></div>
                        <div id="bar-l3" class="viz-l3" style="width: 10%"></div>
                    </div>
                </div>
                <div class="grid">
                    <div class="card"><div class="metric-label">Layer 1 (Gas)</div><div class="metric-value">Active</div></div>
                    <div class="card"><div class="metric-label">Layer 2 (Liquid)</div><div id="layer2-count" class="metric-value">0</div></div>
                    <div class="card"><div class="metric-label">Layer 3 (Ice)</div><div id="layer3-count" class="metric-value">0</div></div>
                </div>
            </div>

            <div id="learning-tab" class="tab-content">
                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">Crystallization Engine</h3>
                        <span class="tag tag-success">ACTIVE</span>
                    </div>
                    <p style="color: #94a3b8; font-size: 13px;">Configure the background task that graduates Liquid memories into Semantic Ice.</p>
                    <div style="margin: 20px 0;">
                        <div class="flex-between mb-10"><span style="color: #94a3b8; font-size: 13px;">Batch Size</span><input type="number" id="input-batch-size" style="width: 80px; background: #020617; border: 1px solid var(--border); color: white; padding: 4px;"></div>
                        <div class="flex-between mb-10"><span style="color: #94a3b8; font-size: 13px;">Interval (Hours)</span><input type="number" step="0.1" id="input-interval" style="width: 80px; background: #020617; border: 1px solid var(--border); color: white; padding: 4px;"></div>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn" style="flex: 1; background: #334155; color: white;" onclick="saveLearningConfig()">Save</button>
                        <button class="btn" style="flex: 2; background: #a855f7;" onclick="triggerLearning()"><i class="fas fa-crystal-ball"></i> Trigger Now</button>
                    </div>
                    <div id="learning-status" style="font-size: 11px; color: #94a3b8; margin-top: 12px; text-align: center;">Crystallization monitoring online.</div>
                </div>
            </div>

            <div id="agents-tab" class="tab-content">
                <h2 style="color: var(--accent);">Agent Orchestration</h2>
                <div class="grid">
                    <div class="card">
                        <div class="card-title">Cognitive Load</div>
                        <div id="agent-load-stats" class="mt-10"></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Empathy & Tone</div>
                        <div id="empathy-stats" class="mt-10"></div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 25px; border-top: 4px solid var(--accent);">
                    <div class="card-title">Layer 1: Cognitive Blackboard (Working Memory)</div>
                    <p style="color: #94a3b8; font-size: 12px; margin-bottom: 15px;">Real-time shared insights between agents in the swarm.</p>
                    <div id="blackboard-feed" style="max-height: 200px; overflow-y: auto;">
                        <div class="metric-label">No active insights on blackboard.</div>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 25px; border-top: 4px solid var(--accent);">
                    <div class="card-title">Swarm Command Console</div>
                    <p style="color: #94a3b8; font-size: 12px; margin-bottom: 15px;">Inject a query directly into the cognitive mesh to observe agent negotiation.</p>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="swarm-query-input" placeholder="e.g. Heart rate spike detected in patient room 4" class="input-field" style="margin:0; flex:1;">
                        <button class="btn" onclick="triggerSwarm()"><i class="fas fa-play"></i> Ignite Swarm</button>
                    </div>
                </div>
                <div class="card" style="margin-bottom: 25px; border-top: 4px solid #a855f7;">
                    <div class="card-title">Chain-of-Thought (CoT) Negotiation Swarm</div>
                    <p style="color: #94a3b8; font-size: 12px; margin-bottom: 15px;">Visualizing multi-agent reasoning paths for complex scenarios.</p>
                    <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                        <div id="mermaid-graph-container" style="background: #020617; border-radius: 8px; padding: 20px; overflow-x: auto; flex: 3; min-width: 300px; display: flex; justify-content: center; min-height: 250px;">
                            <div class="metric-label">Awaiting negotiation signal...</div>
                        </div>
                        <div id="swarm-thought-terminal" style="background: #020617; border: 1px solid var(--border); border-radius: 8px; padding: 15px; flex: 2; min-width: 300px; height: 250px; display: flex; flex-direction: column; font-family: monospace; font-size: 12px; color: #34d399; position: relative;">
                            <div style="position: sticky; top: -15px; background: #020617; padding-bottom: 5px; border-bottom: 1px solid #1e293b; color: #64748b; font-weight: bold; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; display: flex; justify-content: space-between;"><span>> Live Swarm Feed</span><i class="fas fa-terminal"></i></div>
                            <div id="thought-log" style="flex: 1; overflow-y: auto; margin-bottom: 10px;">
                                <div style="color: #64748b; font-style: italic;">> Initialize Live Swarm Feed...</div>
                            </div>
                            <div id="terminal-input-row" style="display: flex; gap: 8px; border-top: 1px solid #1e293b; padding-top: 10px; align-items: center;">
                                <span style="color: #64748b;">@</span>
                                <input type="text" id="terminal-target" value="Orchestrator" style="width: 70px; background: transparent; border: none; color: #38bdf8; font-family: monospace; font-size: 11px; outline: none;">
                                <input type="text" id="terminal-input" placeholder="Steer swarm..." style="flex: 1; background: transparent; border: none; color: #f1f5f9; font-family: monospace; font-size: 11px; outline: none;" onkeydown="if(event.key==='Enter') sendSwarmSteering()">
                                <button onclick="sendSwarmSteering()" style="background: transparent; border: none; color: #34d399; cursor: pointer; padding: 0;"><i class="fas fa-paper-plane"></i></button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title">HITL / Pending Actions</div>
                    <div id="hitl-list" class="mt-10">
                        <div class="metric-label" style="text-align: center; padding: 20px;">No pending Human-In-The-Loop requests.</div>
                    </div>
                </div>
            </div>

            <div id="mcp-tab" class="tab-content">
                <h2 style="color: var(--accent);">Model Context Protocol (MCP) Registry</h2>
                <div class="grid">
                    <div class="card">
                        <div class="card-title">Registered Nodes</div>
                        <div id="mcp-servers-list" class="mt-10"></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Available Swarm Tools</div>
                        <div id="mcp-tools-list" class="mt-10"></div>
                    </div>
                    <div class="card">
                        <div class="card-title">Exposed Resources (L3)</div>
                        <div id="mcp-resources-list" class="mt-10"></div>
                    </div>
                    <div class="card" style="grid-column: span 3; border-top: 4px solid var(--success);">
                        <div class="card-title">MCP Protocol Tester</div>
                        <p style="color: #94a3b8; font-size: 12px; margin-bottom: 15px;">Manually execute protocol tool-calls to verify vault decoupling.</p>
                        <div style="display: flex; gap: 10px;">
                            <select id="mcp-test-tool" class="input-field" style="margin:0; flex:1;"><option value="vault_search">vault_search</option><option value="vault_add">vault_add</option><option value="blackboard_post">blackboard_post</option></select>
                            <input type="text" id="mcp-test-args" placeholder='{"query": "health data"}' class="input-field" style="margin:0; flex:2;">
                            <button class="btn" onclick="executeMcpTest()">Run Tool Call</button>
                        </div>
                        <pre id="mcp-test-output" style="margin-top:15px; display:none;"></pre>
                    </div>
                </div>
            </div>

            <div id="logs-tab" class="tab-content">
                <div class="card" style="height: calc(100vh - 200px); display: flex; flex-direction: column;">
                    <div class="flex-between mb-10">
                        <h3 style="margin:0; color: #34d399;">Live Engine Logs</h3>
                        <button class="refresh-btn" onclick="document.getElementById('log-container').innerHTML = ''"><i class="fas fa-eraser"></i> Clear View</button>
                    </div>
                    <div id="log-container" class="log-container"></div>
                </div>
            </div>

            <div id="governance-tab" class="tab-content">
                <h2 style="color: var(--accent);">Governance & Audit</h2>
                <div class="card" style="margin-bottom: 25px; border-left: 4px solid #f87171;">
                    <div class="flex-between">
                        <div>
                            <h3 class="card-title">VeriLinkOS Execution Kernel</h3>
                            <p id="verilink-desc" style="color: #94a3b8; font-size: 12px; margin-top: 5px;">Currently in fail-soft mode.</p>
                        </div>
                        <button class="btn" id="verilink-toggle-btn" onclick="toggleVeriLinkMode()"><i class="fas fa-plug-circle-xmark"></i> Suppress Connection</button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header"><h3 class="card-title">Action Chain & VAP Receipts</h3></div>
                    <div id="audit-container" style="max-height: 400px; overflow-y: auto;">
                        <div class="metric-label">Loading audit trail...</div>
                    </div>
                </div>
            </div>

            <div id="security-tab" class="tab-content">
                <h2 style="color: var(--accent);">Privacy Vault</h2>
                <div class="card" id="security-status-card">
                    <div class="metric-label">Loading vault security status...</div>
                </div>
            </div>
        </main>
    </div>

    <div id="toast-container" class="toast-container"></div>

    <div id="details-modal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeModal()">&times;</span>
            <h2 style="color: var(--accent); margin-top: 0; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-microchip"></i> Orchestrator State Snapshot
            </h2>
            <hr style="border: 0; border-top: 1px solid var(--border); margin: 20px 0;">
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        let logSource = null;
        let ws = null;
        let currentHitlData = [];
        mermaid.initialize({ startOnLoad: false, theme: 'dark', securityLevel: 'loose' });

        function switchTab(event, tabId) {
            document.querySelectorAll('.nav-item').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            event.currentTarget.classList.add('active');
            document.getElementById(tabId + '-tab').classList.add('active');
            if (tabId === 'logs') startLogStream();
            if (tabId === 'models') fetchInstalledModels();
            if (tabId === 'learning') fetchLearningConfig();
            if (tabId === 'governance') fetchGovernanceLogs();
            if (tabId === 'agents') fetchAgentStatus();
            if (tabId === 'mcp') fetchMcpRegistry();
        }

       function showToast(message, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            const icon = type === 'success' ? 'fa-circle-check' : (type === 'error' ? 'fa-triangle-exclamation' : 'fa-circle-info');
            toast.innerHTML = `<i class="fas ${icon}"></i> <span>${message}</span>`;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(20px)';
                setTimeout(() => toast.remove(), 300);
            }, 4000);
        }

        function startLogStream() {
            if (logSource) logSource.close();
            const container = document.getElementById('log-container');
            container.innerHTML = '';
            logSource = new EventSource('/api/v1/admin/dashboard/logs/stream');
            logSource.onmessage = function(e) {
                const line = document.createElement('div');
                line.textContent = e.data;
                if (e.data.includes('ERROR')) line.className = 'log-line-error';
                else if (e.data.includes('WARNING')) line.className = 'log-line-warning';
                else if (e.data.includes('INFO')) line.className = 'log-line-info';
                container.appendChild(line);
                container.scrollTop = container.scrollHeight;
            };
        }

        function connectWebSocket() {
            if (ws) ws.close();
            const clientId = 'admin_' + Math.random().toString(36).substring(7);
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // Proxied via /api/v1 prefix in main.py
            ws = new WebSocket(`${protocol}//${window.location.host}/api/v1/admin/dashboard/ws/${clientId}`);
            
            ws.onopen = () => {
                console.log('✅ Dashboard WebSocket connected successfully');
            };
            
            ws.onmessage = function(e) {
                const data = JSON.parse(e.data);
                console.log('📥 WebSocket Signal Received:', data.type, data);
                
                if (data.type === 'iot_update') {
                    // This is handled by throttledFetch to keep UI in sync with DB
                    console.log('IoT Signal: Orchestrator Pulse');
                    throttledFetch();
                } else if (data.type === 'metrics_update') {
                    throttledFetch();
                } else if (data.type === 'thought_stream') {
                    appendThought(data.agent, data.content);
                }
                
                const secContainer = document.getElementById('security-status-card');
                if (secContainer && data.security) {
                    secContainer.innerHTML = `
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Encryption Status</span><span style="color: #34d399;">✅ ${data.security.encryption}</span></div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Tokenization</span><span style="color: #34d399;">✅ ${data.security.tokenization}</span></div>
                    `;
                }
            };
            ws.onclose = () => { 
                console.log('❌ Dashboard WebSocket disconnected. Retrying in 5s...');
                setTimeout(connectWebSocket, 5000); 
            };
            ws.onerror = (err) => {
                console.error('⚠️ WebSocket Connection Error:', err);
            };
        }

        function appendThought(agent, content) {
            const log = document.getElementById('thought-log');
            if (!log) return;
            const div = document.createElement('div');
            div.style.marginBottom = '8px';
            div.style.animation = 'fadeIn 0.2s ease-out';
            div.innerHTML = `<span style="color: #38bdf8; font-weight: bold; cursor: pointer;" onclick="document.getElementById('terminal-target').value='${agent}'">[${agent}]</span> <span style="color: #f1f5f9;">${content}</span>`;
            log.appendChild(div);
            log.scrollTop = log.scrollHeight;
        }

        async function sendSwarmSteering() {
            const targetEl = document.getElementById('terminal-target');
            const inputEl = document.getElementById('terminal-input');
            const agent = targetEl.value;
            const content = inputEl.value.trim();
            if (!content) return;
            
            const res = await fetch('/api/v1/admin/dashboard/swarm/respond', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ agent, content })
            });
            
            if (res.ok) { inputEl.value = ''; }
        }

        let lastFetch = 0;
        let fetchInProgress = false;
        function throttledFetch() {
            const now = Date.now();
            if (fetchInProgress || now - lastFetch < 5000) return;
            fetchMetrics();
            // Auto-refresh orchestration view if active
            if (document.getElementById('agents-tab').classList.contains('active')) fetchAgentStatus();
        }

        async function fetchMetrics() {
            lastFetch = Date.now();
            fetchInProgress = true;
            try {
                const res = await fetch('/api/v1/admin/dashboard/metrics');
                const data = await res.json();
                document.getElementById('raw-metrics').textContent = JSON.stringify(data, null, 2);
                
                const secContainer = document.getElementById('security-status-card');
                if (secContainer && data.security) {
                    secContainer.innerHTML = `
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Encryption Status</span><span style="color: #34d399;">✅ ${data.security.encryption}</span></div>
                        <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #334155;"><span style="color: #94a3b8;">Tokenization</span><span style="color: #34d399;">✅ ${data.security.tokenization}</span></div>
                    `;
                }

                const vBtn = document.getElementById('verilink-toggle-btn');
                const vDesc = document.getElementById('verilink-desc');
                if (data.ai?.verilink_offline) {
                    vBtn.innerHTML = '<i class="fas fa-plug-circle-check"></i> Resume Connection';
                    vBtn.style.background = '#34d399';
                    vDesc.innerText = 'VeriLink connection attempts are manually suppressed.';
                } else {
                    vBtn.innerHTML = '<i class="fas fa-plug-circle-xmark"></i> Suppress Connection';
                    vBtn.style.background = '#f87171';
                    vDesc.innerText = 'System is attempting to synchronize with VeriLinkOS.';
                }

                const grid = document.getElementById('metrics-grid');
                grid.innerHTML = `
                    <div class="card"><div class="metric-label"><i class="fas fa-users"></i> Users</div><div class="metric-value">${data.users?.total || 0}</div></div>
                    <div class="card"><div class="metric-label"><i class="fas fa-brain"></i> Memories</div><div class="metric-value">${data.memories?.total || 0}</div></div>
                    <div class="card"><div class="metric-label">Ollama</div><div class="metric-value" style="font-size:20px;">${data.ai?.ollama_status || 'unknown'}</div></div>
                    <div class="card"><div class="metric-label">Vector Index</div><div class="metric-value">${data.system?.vector_index_size || 0}</div></div>
                    <div class="card"><div class="metric-label">Active Sessions</div><div class="metric-value">${data.sessions?.active || 0}</div></div>
                    <div class="card"><div class="metric-label">Legal Matters</div><div class="metric-value" style="color:var(--accent);">${data.legal?.active_matters || 0}</div></div>
                    <div class="card">
                        <div class="metric-label">Active IoT Devices</div>
                        <div class="metric-value">${data.iot?.active_count || 0}</div>
                        <div style="font-size: 11px; color: #94a3b8; line-height: 1.4; margin-top: 5px;">
                            ${data.iot?.active_devices?.length > 0 ? data.iot.active_devices.join(', ') : 'None'}
                        </div>
                    </div>
                    <div class="card"><div class="metric-label">IoT Telemetry Points</div><div class="metric-value" style="color:#34d399;">${data.iot?.data_points_today || 0}</div></div>
                `;

                if (document.getElementById('layer2-count')) {
                    const l2Count = data.memories?.total || 0;
                    const l3Count = data.system?.vector_index_size || 0;
                    document.getElementById('layer2-count').innerText = l2Count;
                    document.getElementById('layer3-count').innerText = l3Count;
                    const total = (l2Count + l3Count) || 1;
                    document.getElementById('bar-l2').style.width = ((l2Count / total) * 100) + '%';
                    document.getElementById('bar-l3').style.width = ((l3Count / total) * 100) + '%';
                }
            } catch (e) { console.error('Fetch Metrics Error:', e); }
            finally { fetchInProgress = false; }
        }

        async function fetchMcpRegistry() {
            try {
                const res = await fetch('/api/v1/admin/dashboard/mcp/registry');
                const data = await res.json();
                document.getElementById('mcp-servers-list').innerHTML = data.servers.map(s => `<div class="stat-row"><div>${s.name}</div><span class="tag tag-success">${s.status}</span></div>`).join('');
                document.getElementById('mcp-tools-list').innerHTML = data.tools.map(t => `<div style="padding:10px; background:#020617; border:1px solid var(--border); border-radius:8px; margin-bottom:8px;"><b>${t.name}</b><br>${t.description}</div>`).join('');
                document.getElementById('mcp-resources-list').innerHTML = data.resources.map(r => `
                    <div style="padding: 10px; background: #020617; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px;">
                        <div class="flex-between">
                            <span style="font-weight:700; color:#a855f7; font-size:11px;">${r.name}</span>
                            <span class="tag">${r.type}</span>
                        </div>
                        <div style="font-size:10px; color:#64748b; margin-top:4px; font-family:monospace; word-break:break-all;">${r.uri}</div>
                    </div>
                `).join('');
            } catch (e) { showToast('MCP Registry offline', 'error'); }
        }

        async function fetchInstalledModels() {
            const listEl = document.getElementById('models-list');
            try {
                const response = await fetch('/api/v1/admin/dashboard/models');
                const data = await response.json();
                listEl.innerHTML = (data.models || []).map(m => `
                    <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #020617; border: 1px solid var(--border); border-radius: 8px;">
                        <div>
                            <div style="font-weight: 700; color: var(--accent);">${m.name}</div>
                            <div style="font-size: 11px; color: #64748b;">Size: ${(m.size / (1024*1024*1024)).toFixed(2)} GB</div>
                        </div>
                        <button class="refresh-btn" style="color: #f87171; border-color: #f87171; padding: 4px 10px; font-size: 11px;" onclick="deleteModel('${m.name}')">Delete</button>
                    </div>
                `).join('') || '<div class="metric-label">No models installed.</div>';
            } catch (err) { listEl.innerHTML = 'Error loading models'; }
        }

        async function triggerModelPull() {
            const input = document.getElementById('new-model-input');
            const statusEl = document.getElementById('pull-status');
            const name = input.value.trim();
            if (!name) return;
            showToast(`Initiating download for ${name}...`, 'info');
            const response = await fetch('/api/v1/admin/dashboard/models/pull', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name})
            });
            const reader = response.body.getReader();
            while (true) {
                const {value, done} = await reader.read();
                if (done) break;
                statusEl.textContent += new TextDecoder().decode(value).replace(/data: /g, '');
                statusEl.scrollTop = statusEl.scrollHeight;
            }
            showToast(`${name} download complete`, 'success');
            fetchInstalledModels();
        }

        async function deleteModel(name) {
            if (!confirm(`Permanently purge ${name} from local storage?`)) return;
            await fetch(`/api/v1/admin/dashboard/models/${name}`, {method: 'DELETE'});
            fetchInstalledModels();
        }

        async function fetchGovernanceLogs() {
            const container = document.getElementById('audit-container');
            try {
                const res = await fetch('/api/v1/admin/dashboard/governance/logs?limit=20');
                const data = await res.json();
                container.innerHTML = data.logs.map(l => `
                    <div style="padding: 12px 0; border-bottom: 1px solid var(--border);">
                        <div class="flex-between">
                            <span style="font-size:13px; font-weight:600;">${l.query}</span>
                            <span class="tag ${l.hitl ? 'tag-success' : ''}">${l.hitl ? 'HITL' : 'AUTO'}</span>
                        </div>
                        <div style="display: flex; gap: 15px; margin-top: 5px;">
                            <span style="font-size:10px; color: var(--accent); font-family: monospace;">RECEIPT: ${l.receipt}</span>
                            <span style="font-size:10px; color: #64748b;">${new Date(l.timestamp).toLocaleString()}</span>
                        </div>
                    </div>
                `).join('') || '<div class="metric-label">No governance receipts found.</div>';
            } catch (e) { container.innerHTML = 'Error loading logs.'; }
        }

        async function toggleVeriLinkMode() {
            try {
                const res = await fetch('/api/v1/admin/dashboard/governance/toggle-offline', {method: 'POST'});
                const data = await res.json();
                showToast(data.offline_mode ? 'VeriLink connection suppressed' : 'VeriLink reconnection enabled', 'info');
                fetchMetrics();
            } catch (e) { showToast('Error toggling governance mode', 'error'); }
        }

        async function fetchLearningConfig() {
            const res = await fetch('/api/v1/admin/dashboard/learning/config');
            const data = await res.json();
            document.getElementById('input-batch-size').value = data.batch_size;
            document.getElementById('input-interval').value = data.interval_hours;
        }

        async function saveLearningConfig() {
            const batch_size = document.getElementById('input-batch-size').value;
            const interval_hours = document.getElementById('input-interval').value;
            const res = await fetch('/api/v1/admin/dashboard/learning/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({batch_size, interval_hours})
            });
            if (res.ok) showToast('Crystallization parameters synchronized', 'success');
        }

        async function triggerLearning() {
            await fetch('/api/v1/admin/dashboard/learning/trigger', {method: 'POST'});
            showToast('Manual crystallization cycle ignited', 'info');
        }

        async function executeMcpTest() {
            const tool = document.getElementById('mcp-test-tool').value;
            const argsStr = document.getElementById('mcp-test-args').value;
            const outputEl = document.getElementById('mcp-test-output');
            try {
                const res = await fetch(`/api/v1/mcp/tools/call/${tool}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: argsStr });
                const data = await res.json();
                outputEl.style.display = 'block';
                outputEl.textContent = JSON.stringify(data, null, 2);
            } catch (e) { showToast('Execution failure', 'error'); }
        }

        async function toggleSimulation() {
            const btn = document.getElementById('sim-btn');
            try {
                const res = await fetch('/api/v1/admin/dashboard/system/simulate-iot', {method: 'POST'});
                const data = await res.json();
                if (data.status === 'started') {
                    btn.innerHTML = '<i class="fas fa-stop-circle"></i> Terminate Simulation';
                    btn.style.background = '#7f1d1d'; btn.style.color = 'white';
                    showToast('Virtual telemetry stream active', 'success');
                } else {
                    btn.innerHTML = '<i class="fas fa-bolt"></i> Ignite IoT Simulation';
                    btn.style.background = '#38bdf8'; btn.style.color = '#0f172a';
                    showToast('Simulation sensors offline', 'info');
                }
            } catch (e) { showToast('Ignition failure', 'error'); }
        }

        async function approveAction(id) {
            const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/approve`, {method: 'POST'});
            if (res.ok) { showToast('HITL Protocol Approved', 'success'); fetchAgentStatus(); }
        }

        async function denyAction(id) {
            const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/deny`, {method: 'POST'});
            if (res.ok) { showToast('HITL Protocol Rejected', 'error'); fetchAgentStatus(); }
        }

        function showHitlDetails(id) {
            const item = currentHitlData.find(h => h.id == id);
            if (!item) return;
            const body = document.getElementById('modal-body');
            body.innerHTML = `
                <div id="explanation-box" style="display:none; margin-bottom: 25px; padding: 20px; background: rgba(56, 189, 248, 0.05); border: 1px solid var(--accent); border-radius: 8px; border-left-width: 4px;">
                    <div class="metric-label" style="color: var(--accent); margin-bottom: 10px;"><i class="fas fa-comment-nodes"></i> AI Cognitive Insight</div>
                    <div id="explanation-text" style="font-size: 14px; line-height: 1.6; color: #f1f5f9;"></div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 25px;">
                    <div><div class="metric-label">Agent Identity</div><div style="color: #fbbf24; font-weight: 800; font-size: 18px; margin-top: 5px;">${item.agent_type}</div></div>
                    <div><div class="metric-label">Interruption Point</div><div style="color: var(--accent); font-weight: 700; margin-top: 5px;">${item.data?.interruption_point || 'Unknown'}</div></div>
                </div>
                <div style="margin-bottom: 25px;"><div class="metric-label">Critical Observation</div><div style="font-size: 14px; margin-top: 8px; background: #020617; padding: 12px; border-radius: 6px; border: 1px solid #1e293b;">${item.query}</div></div>
                <button class="btn" id="explain-btn" onclick="explainReasoning('${id}')" style="background: var(--accent); width: 100%; margin-bottom: 25px; justify-content: center;"><i class="fas fa-wand-magic-sparkles"></i> Synthesize Reasoning Explanation</button>
                <div class="metric-label">Raw System Context (Internal Data)</div>
                <pre style="margin-top: 10px; border-color: #334155;">${JSON.stringify(item.data, null, 4)}</pre>
            `;
            document.getElementById('details-modal').style.display = 'block';
        }

        async function explainReasoning(id) {
            const btn = document.getElementById('explain-btn');
            const box = document.getElementById('explanation-box');
            const text = document.getElementById('explanation-text');
            btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> AI Reasoning in Progress...';
            try {
                const res = await fetch(`/api/v1/admin/dashboard/hitl/${id}/explain`, { method: 'POST' });
                const data = await res.json();
                box.style.display = 'block'; text.innerText = data.explanation; btn.style.display = 'none';
            } catch (e) {
                showToast('AI Synthesis Failed', 'error');
                btn.innerHTML = '<i class="fas fa-wand-magic-sparkles"></i> Retry Explanation';
                btn.disabled = false;
            }
        }

        function closeModal() { document.getElementById('details-modal').style.display = 'none'; }
        window.onclick = function(event) { if (event.target == document.getElementById('details-modal')) closeModal(); }

        async function fetchAgentStatus() {
            const [loadRes, empathyRes, hitlRes, bbRes] = await Promise.all([
                fetch('/api/v1/admin/dashboard/cognitive-load'),
                fetch('/api/v1/admin/dashboard/empathy/status'),
                fetch('/api/v1/admin/dashboard/hitl/pending'),
                fetch('/api/v1/admin/dashboard/blackboard/snapshot')
            ]);
            const load = await loadRes.json();
            const empathy = await empathyRes.json();
            const hitl = await hitlRes.json();
            const bb = await bbRes.json();
            currentHitlData = hitl;

        // Swarm Trigger Function
        window.triggerSwarm = async function() {
            const input = document.getElementById('swarm-query-input');
            const query = input.value.trim();
            if (!query) return;
            
            // Clear previous thoughts for fresh context
            document.getElementById('thought-log').innerHTML = '';
            
            showToast('Igniting agent swarm...', 'info');
            const res = await fetch('/api/v1/admin/dashboard/swarm/trigger', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ query })
            });
            if (res.ok) { input.value = ''; fetchAgentStatus(); }
        };

        // Swarm CoT Graph Rendering
        try {
            const traceRes = await fetch('/api/v1/admin/dashboard/swarm/negotiation-trace');
            const traceData = await traceRes.json();
            const container = document.getElementById('mermaid-graph-container');
            
            if (traceData.sequence && traceData.sequence.length > 0) {
                let graphDef = 'graph LR\\n';
                graphDef += 'classDef agentNode fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#fff;\\n';
                graphDef += 'classDef bbNode fill:#0f172a,stroke:#a855f7,stroke-width:2px,stroke-dasharray: 5 5;\\n';
                
                traceData.sequence.forEach(step => {
                    // Sanitize IDs for Mermaid compatibility (alphanumeric only)
                    const fromId = step.agent.replace(/[^a-zA-Z0-9]/g, '');
                    const toId = step.to.replace(/[^a-zA-Z0-9]/g, '');
                    graphDef += `${fromId}("${step.agent}") -- "${step.action}" --> ${toId}("${step.to}")\\n`;
                    graphDef += `class ${fromId} agentNode;\\n`;
                    if (toId === 'Blackboard') graphDef += `class ${toId} bbNode;\\n`;
                });
                container.innerHTML = `<div class="mermaid">${graphDef}</div>`;
                mermaid.init(undefined, container.querySelectorAll('.mermaid'));
            }
        } catch (err) { console.error('CoT Graph Error:', err); }            

            let agentHtml = `<div class="stat-row"><span>Active Tasks</span><span>${load.active_tasks}</span></div>`;
            for (const [name, count] of Object.entries(load.agent_activity || {})) {
                agentHtml += `<div class="stat-row"><span>${name} Agent</span><span class="tag ${count > 0 ? 'tag-success' : ''}">${count > 0 ? 'ACTIVE' : 'IDLE'}</span></div>`;
            }
            document.getElementById('agent-load-stats').innerHTML = agentHtml;

            document.getElementById('empathy-stats').innerHTML = `
                <div class="stat-row"><span>Mood</span><span>${empathy.mood}</span></div>
                <div class="stat-row"><span>Tone</span><span>${empathy.tone}</span></div>
            `;
            
            const bbEl = document.getElementById('blackboard-feed');
            const bbEntries = Object.entries(bb.current_state || {});
            bbEl.innerHTML = bbEntries.length ? bbEntries.map(([agent, entry]) => `
                <div class="stat-row" style="flex-direction:column; align-items:flex-start;">
                    <div class="flex-between" style="width:100%;"><b>${agent.toUpperCase()}</b> <small>${new Date(entry.timestamp).toLocaleTimeString()}</small></div>
                    <div style="font-size:12px; color: #94a3b8;">${JSON.stringify(entry.data)}</div>
                </div>
            `).join('') : 'No active insights.';

            const hitlEl = document.getElementById('hitl-list');
            hitlEl.innerHTML = hitl.length ? hitl.map(h => `
                <div class="card" style="margin-bottom:10px; background:#020617;">
                    <div class="flex-between"><b>${h.agent_type} Intervention</b> <small>${new Date(h.timestamp).toLocaleTimeString()}</small></div>
                    <div style="font-size:13px; margin:12px 0; color:#f1f5f9;">${h.query}</div>
                    <div style="display:flex; gap:10px;">
                        <button class="btn" style="padding:4px 10px;" onclick="approveAction('${h.id}')">Approve</button>
                        <button class="btn" style="padding:4px 10px; background:#7f1d1d;" onclick="denyAction('${h.id}')">Deny</button>
                        <button class="btn" style="padding:4px 10px; background:#334155;" onclick="showHitlDetails('${h.id}')">Details</button>
                    </div>
                </div>
            `).join('') : 'No pending actions.';
        }

        async function logout() {
            await fetch('/api/v1/auth/logout', { method: 'POST' });
            window.location.href = '/login';
        }

        fetchMetrics();
        connectWebSocket();
        setInterval(fetchMetrics, 60000);
    </script>
</body>
</html>
"""