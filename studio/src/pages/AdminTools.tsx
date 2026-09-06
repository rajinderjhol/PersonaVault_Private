import React, { useState, useEffect, useRef } from 'react';
import { useV2SystemHealth, useV2ExecutionMode, useV2Logs } from '../hooks/query/v2/useV2Admin';
import styles from './AdminTools.module.css';

export const AdminTools: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'health' | 'services' | 'logs' | 'mode'>('health');
  const [logLevel, setLogLevel] = useState<string>('all');
  const logContainerRef = useRef<HTMLDivElement>(null);

  const { data: health, isLoading, refetch } = useV2SystemHealth();
  const { data: logs, isLoading: logsLoading } = useV2Logs({ limit: 100, level: logLevel === 'all' ? undefined : logLevel });
  const { mutate: setMode, isLoading: isModeLoading } = useV2ExecutionMode();

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (logContainerRef.current && logs) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'info': return 'ℹ️';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      case 'debug': return '🔍';
      default: return '📝';
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🛠️ Admin & Dev Tools</h1>
        <p>System health, service registry, and operational controls</p>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabs}>
        {['health', 'services', 'logs', 'mode'].map((tab) => (
          <button
            key={tab}
            className={`${styles.tab} ${activeTab === tab ? styles.active : ''}`}
            onClick={() => setActiveTab(tab as any)}
          >
            {tab === 'health' && '📊 Health'}
            {tab === 'services' && '🔌 Services'}
            {tab === 'logs' && '📋 Logs'}
            {tab === 'mode' && '⚙️ Mode'}
          </button>
        ))}
      </div>

      {/* Health Tab */}
      {activeTab === 'health' && (
        <div className={styles.tabContent}>
          <div className={styles.healthGrid}>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>Status</span>
              <span className={`${styles.healthValue} ${health?.status ? styles[health.status] : ''}`}>
                {health?.status || 'Loading...'}
              </span>
            </div>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>Uptime</span>
              <span className={styles.healthValue}>{health?.uptime || 'N/A'}</span>
            </div>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>Memory</span>
              <span className={styles.healthValue}>
                {health?.memory ? `${health.memory.used}MB / ${health.memory.total}MB (${health.memory.percentage}%)` : 'N/A'}
              </span>
            </div>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>CPU</span>
              <span className={styles.healthValue}>
                {health?.cpu ? `${health.cpu.usage}% (${health.cpu.cores} cores)` : 'N/A'}
              </span>
            </div>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>WebSocket</span>
              <span className={styles.healthValue}>
                {health?.websocket ? `${health.websocket.connections} connections` : 'N/A'}
              </span>
            </div>
            <div className={styles.healthCard}>
              <span className={styles.healthLabel}>Mode</span>
              <span className={styles.healthValue}>
                {health?.mode || 'standard'}
              </span>
            </div>
          </div>
          <button onClick={() => refetch()} className={styles.refreshButton}>
            🔄 Refresh
          </button>
        </div>
      )}

      {/* Services Tab */}
      {activeTab === 'services' && (
        <div className={styles.tabContent}>
          <h2>🔌 Service Registry</h2>
          {isLoading ? (
            <div className={styles.loading}>Loading services...</div>
          ) : (
            <div className={styles.servicesList}>
              {health?.services?.length === 0 ? (
                <div className={styles.emptyState}>
                  <span>🔌</span>
                  <p>No services registered</p>
                  <p className={styles.emptySubtext}>Services will appear here when they register</p>
                </div>
              ) : (
                health?.services?.map((service, index) => (
                  <div key={index} className={styles.serviceCard}>
                    <div className={styles.serviceInfo}>
                      <span className={styles.serviceName}>{service.name}</span>
                      {service.version && (
                        <span className={styles.serviceVersion}>v{service.version}</span>
                      )}
                    </div>
                    <span className={`${styles.serviceStatus} ${service.status === 'running' ? styles.running : styles.stopped}`}>
                      {service.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div className={styles.tabContent}>
          <h2>📋 Log Viewer</h2>
          <div className={styles.logViewer}>
            <div className={styles.logControls}>
              <div className={styles.logControlsLeft}>
                <button className={styles.logButton}>▶️ Start</button>
                <button className={styles.logButton}>⏹️ Stop</button>
                <button className={styles.logButton}>🗑️ Clear</button>
              </div>
              <div className={styles.logControlsRight}>
                <select
                  value={logLevel}
                  onChange={(e) => setLogLevel(e.target.value)}
                  className={styles.logFilter}
                >
                  <option value="all">All Levels</option>
                  <option value="info">ℹ️ Info</option>
                  <option value="warning">⚠️ Warning</option>
                  <option value="error">❌ Error</option>
                  <option value="debug">🔍 Debug</option>
                </select>
              </div>
            </div>
            <div className={styles.logContainer} ref={logContainerRef}>
              {logsLoading ? (
                <div className={styles.logLoading}>Loading logs...</div>
              ) : logs?.length === 0 ? (
                <div className={styles.logEmpty}>No logs available</div>
              ) : (
                logs?.map((log, index) => (
                  <div key={index} className={`${styles.logEntry} ${styles[log.level]}`}>
                    <span className={styles.logTime}>[{log.timestamp}]</span>
                    <span className={styles.logLevel}>{getLevelIcon(log.level)} {log.level.toUpperCase()}</span>
                    {log.source && <span className={styles.logSource}>[{log.source}]</span>}
                    <span className={styles.logMessage}>{log.message}</span>
                    {log.details && (
                      <span className={styles.logDetails}>
                        {JSON.stringify(log.details)}
                      </span>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Execution Mode Tab */}
      {activeTab === 'mode' && (
        <div className={styles.tabContent}>
          <h2>⚙️ Execution Mode</h2>
          <div className={styles.modeControls}>
            <p className={styles.modeDescription}>
              Switch the execution mode to control system behavior and restrictions.
            </p>
            <div className={styles.modeButtons}>
              {['standard', 'restricted', 'simulation', 'audit'].map((mode) => (
                <button
                  key={mode}
                  className={`${styles.modeButton} ${health?.mode === mode ? styles.active : ''}`}
                  onClick={() => setMode(mode as any)}
                  disabled={isModeLoading}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
            <div className={styles.modeInfo}>
              <p><strong>Current Mode:</strong> {health?.mode || 'standard'}</p>
              <p className={styles.modeHint}>
                {health?.mode === 'standard' && '✅ All features enabled. Full access to all memory layers and actions.'}
                {health?.mode === 'restricted' && '🔒 Restricted mode. Only Ice-layer memory access. No mutations.'}
                {health?.mode === 'simulation' && '🧪 Simulation mode. All actions are simulated. No live changes.'}
                {health?.mode === 'audit' && '📋 Audit mode. Read-only with full logging of all access.'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
