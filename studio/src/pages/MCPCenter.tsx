import React, { useState, useEffect } from 'react';
import { v2ApiClient } from '../api/v2Client';
import styles from './MCPCenter.module.css';

interface MCPServer {
  id: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error' | 'unknown';
  tools: string[];
  description: string;
  enabled: boolean;
}

export const MCPCenter: React.FC = () => {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [toolResult, setToolResult] = useState<string | null>(null);
  const [showInstallModal, setShowInstallModal] = useState(false);

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    setLoading(true);
    try {
      const response = await v2ApiClient.get<{ servers: MCPServer[] }>('/mcp/servers');
      setServers(response.servers);
    } catch (error) {
      console.error('Failed to load MCP servers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (serverId: string) => {
    try {
      const result = await v2ApiClient.post(`/mcp/servers/${serverId}/connect`, {});
      if (result.success) {
        await loadServers();
      }
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  const handleDisconnect = async (serverId: string) => {
    try {
      const result = await v2ApiClient.post(`/mcp/servers/${serverId}/disconnect`, {});
      if (result.success) {
        await loadServers();
      }
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  };

  const handleCallTool = async (serverId: string, toolName: string, params: any = {}) => {
    try {
      setToolResult('⏳ Calling tool...');
      const result = await v2ApiClient.post(
        `/mcp/servers/${serverId}/tools/${toolName}`,
        params
      );
      setToolResult(JSON.stringify(result, null, 2));
    } catch (error) {
      setToolResult(`❌ Error: ${error}`);
    }
  };

  const handleUninstall = async (serverId: string) => {
    if (!confirm(`Are you sure you want to uninstall ${serverId}?`)) return;
    try {
      await v2ApiClient.delete(`/mcp/servers/${serverId}`);
      await loadServers();
    } catch (error) {
      console.error('Failed to uninstall:', error);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <h1>🔌 MCP Center</h1>
          <p>Manage Model Context Protocol servers and tools</p>
        </div>
        <button 
          className={styles.installButton}
          onClick={() => setShowInstallModal(true)}
        >
          + Install Server
        </button>
      </div>

      {/* Server Grid */}
      <div className={styles.serversGrid}>
        {servers.map(server => (
          <div 
            key={server.id} 
            className={`${styles.serverCard} ${server.status === 'connected' ? styles.connected : ''}`}
          >
            <div className={styles.serverHeader}>
              <div className={styles.serverInfo}>
                <span className={styles.serverIcon}>🌐</span>
                <span className={styles.serverName}>{server.name}</span>
              </div>
              <div className={styles.serverStatus}>
                <span className={`${styles.statusDot} ${styles[server.status]}`} />
                <span className={styles.statusText}>{server.status}</span>
              </div>
            </div>

            <p className={styles.serverDescription}>{server.description}</p>

            <div className={styles.serverTools}>
              <span className={styles.toolsLabel}>🛠️ Tools:</span>
              <div className={styles.toolsList}>
                {server.tools.map(tool => (
                  <button
                    key={tool}
                    className={styles.toolButton}
                    onClick={() => handleCallTool(server.id, tool, {})}
                    disabled={server.status !== 'connected'}
                  >
                    {tool}
                  </button>
                ))}
              </div>
            </div>

            <div className={styles.serverActions}>
              {server.status === 'connected' ? (
                <button 
                  className={styles.disconnectButton}
                  onClick={() => handleDisconnect(server.id)}
                >
                  Disconnect
                </button>
              ) : (
                <button 
                  className={styles.connectButton}
                  onClick={() => handleConnect(server.id)}
                  disabled={!server.enabled}
                >
                  Connect
                </button>
              )}
              <button 
                className={styles.uninstallButton}
                onClick={() => handleUninstall(server.id)}
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Tool Result Panel */}
      {toolResult && (
        <div className={styles.resultPanel}>
          <div className={styles.resultHeader}>
            <h3>Tool Result</h3>
            <button 
              className={styles.closeButton}
              onClick={() => setToolResult(null)}
            >
              ×
            </button>
          </div>
          <pre className={styles.resultContent}>{toolResult}</pre>
        </div>
      )}

      {/* Install Modal */}
      {showInstallModal && (
        <div className={styles.modal}>
          <div className={styles.modalContent}>
            <h2>Install MCP Server</h2>
            <form id="install-form" className={styles.installForm}>
              <div className={styles.formGroup}>
                <label>Server ID</label>
                <input
                  type="text"
                  name="id"
                  placeholder="e.g., local-shell"
                  className={styles.formInput}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Name</label>
                <input
                  type="text"
                  name="name"
                  placeholder="e.g., Local Shell"
                  className={styles.formInput}
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label>Description</label>
                <input
                  type="text"
                  name="description"
                  placeholder="Brief description of the server"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Command</label>
                <input
                  type="text"
                  name="command"
                  placeholder="e.g., python"
                  className={styles.formInput}
                  defaultValue="python"
                />
              </div>
              <div className={styles.formGroup}>
                <label>Arguments</label>
                <input
                  type="text"
                  name="args"
                  placeholder="e.g., -m search_mcp"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Working Directory</label>
                <input
                  type="text"
                  name="cwd"
                  placeholder="Absolute path to server directory"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>Tools (comma separated)</label>
                <input
                  type="text"
                  name="tools"
                  placeholder="e.g., search, fetch, research"
                  className={styles.formInput}
                />
              </div>
              <div className={styles.formGroup}>
                <label>
                  <input type="checkbox" name="enabled" defaultChecked />
                  Enable server
                </label>
              </div>
            </form>
            <div className={styles.modalActions}>
              <button 
                className={styles.cancelButton}
                onClick={() => setShowInstallModal(false)}
              >
                Cancel
              </button>
              <button 
                className={styles.installFormButton}
                onClick={(e) => {
                  const form = document.getElementById('install-form');
                  const data = new FormData(form as HTMLFormElement);
                  // TODO: Submit form data
                  setShowInstallModal(false);
                }}
              >
                Install
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
