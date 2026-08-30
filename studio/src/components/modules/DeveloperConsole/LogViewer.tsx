import React, { useState, useEffect, useRef } from 'react';
import { useLogs } from '../../../hooks/useLogs';

type LogLevel = 'all' | 'info' | 'warning' | 'error' | 'debug';

export const LogViewer: React.FC = () => {
  const [filter, setFilter] = useState<LogLevel>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  const { logs, isStreaming, isLoading, startStream, stopStream, clearLogs } = useLogs();
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    startStream();
    return () => stopStream();
  }, []);

  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filteredLogs = logs.filter(log => {
    const matchesFilter = filter === 'all' || log.level === filter;
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'log-error';
      case 'warning': return 'log-warning';
      case 'info': return 'log-info';
      case 'debug': return 'log-debug';
      default: return 'log-info';
    }
  };

  return (
    <div className="log-viewer">
      {/* Controls */}
      <div className="log-controls">
        <div className="log-filters">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            All
          </button>
          <button 
            className={filter === 'info' ? 'active' : ''}
            onClick={() => setFilter('info')}
          >
            Info
          </button>
          <button 
            className={filter === 'warning' ? 'active' : ''}
            onClick={() => setFilter('warning')}
          >
            Warning
          </button>
          <button 
            className={filter === 'error' ? 'active' : ''}
            onClick={() => setFilter('error')}
          >
            Error
          </button>
          <button 
            className={filter === 'debug' ? 'active' : ''}
            onClick={() => setFilter('debug')}
          >
            Debug
          </button>
        </div>
        <div className="log-actions">
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <label>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
            />
            Auto-scroll
          </label>
          <button onClick={clearLogs}>Clear</button>
          <button onClick={isStreaming ? stopStream : startStream}>
            {isStreaming ? '⏸ Pause' : '▶ Stream'}
          </button>
        </div>
      </div>

      {/* Logs */}
      <div className="log-container" ref={logContainerRef}>
        {isLoading && <div className="log-loading">Loading logs...</div>}
        {filteredLogs.length === 0 && (
          <div className="log-empty">No logs match the current filters</div>
        )}
        {filteredLogs.map((log, index) => (
          <div key={index} className={`log-entry ${getLogLevelColor(log.level)}`}>
            <span className="log-timestamp">{log.timestamp}</span>
            <span className="log-level">[{log.level.toUpperCase()}]</span>
            <span className="log-source">{log.source}</span>
            <span className="log-message">{log.message}</span>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="log-stats">
        <span>Total: {logs.length} entries</span>
        <span>Errors: {logs.filter(l => l.level === 'error').length}</span>
        <span>Warnings: {logs.filter(l => l.level === 'warning').length}</span>
        <span>Status: {isStreaming ? '🟢 Live' : '⏸ Paused'}</span>
      </div>
    </div>
  );
};
