import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';

interface CrystallizationConfig {
  auto_crystallize: boolean;
  min_confidence: number;
  min_occurrences: number;
  max_age_days: number;
  batch_size: number;
}

interface CrystallizationStats {
  total_patterns: number;
  crystallized: number;
  pending: number;
  rate: number;
  last_run: string | null;
}

export const CrystallizationControls: React.FC = () => {
  const [config, setConfig] = useState<CrystallizationConfig | null>(null);
  const [stats, setStats] = useState<CrystallizationStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchStats, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      await Promise.all([fetchConfig(), fetchStats()]);
    } catch (error) {
      console.error('Failed to fetch crystallization data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchConfig = async () => {
    const response = await apiClient.get('/admin/learning/config');
    setConfig(response.data);
  };

  const fetchStats = async () => {
    const response = await apiClient.get('/admin/learning/stats');
    setStats(response.data);
  };

  const updateConfig = async (key: string, value: any) => {
    try {
      await apiClient.post('/admin/learning/config', { [key]: value });
      setMessage({ type: 'success', text: 'Configuration updated' });
      await fetchConfig();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update configuration' });
    }
  };

  const triggerCrystallization = async () => {
    setIsTriggering(true);
    setMessage(null);
    try {
      await apiClient.post('/admin/learning/crystallization/trigger');
      setMessage({ type: 'success', text: 'Crystallization triggered successfully' });
      await fetchStats();
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to trigger crystallization' });
    } finally {
      setIsTriggering(false);
    }
  };

  if (isLoading) {
    return <div className="crystallization-loading">Loading crystallization controls...</div>;
  }

  return (
    <div className="crystallization-controls">
      {/* Stats */}
      {stats && (
        <div className="crystallization-stats">
          <div className="stat-card">
            <span className="stat-label">Total Patterns</span>
            <span className="stat-value">{stats.total_patterns}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Crystallized</span>
            <span className="stat-value">{stats.crystallized}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Pending</span>
            <span className="stat-value">{stats.pending}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">Rate</span>
            <span className="stat-value">{stats.rate}%</span>
          </div>
        </div>
      )}

      {/* Controls */}
      {config && (
        <div className="crystallization-config">
          <h4>⚙️ Crystallization Settings</h4>
          
          <div className="config-group">
            <label>
              <span>Auto-Crystallize</span>
              <input
                type="checkbox"
                checked={config.auto_crystallize}
                onChange={(e) => updateConfig('auto_crystallize', e.target.checked)}
              />
            </label>
          </div>

          <div className="config-group">
            <label>
              <span>Minimum Confidence</span>
              <input
                type="range"
                min="0.5"
                max="1.0"
                step="0.05"
                value={config.min_confidence}
                onChange={(e) => updateConfig('min_confidence', parseFloat(e.target.value))}
              />
              <span className="config-value">{config.min_confidence}</span>
            </label>
          </div>

          <div className="config-group">
            <label>
              <span>Minimum Occurrences</span>
              <input
                type="number"
                min="1"
                max="10"
                value={config.min_occurrences}
                onChange={(e) => updateConfig('min_occurrences', parseInt(e.target.value))}
              />
            </label>
          </div>

          <div className="config-group">
            <label>
              <span>Max Age (days)</span>
              <input
                type="number"
                min="1"
                max="90"
                value={config.max_age_days}
                onChange={(e) => updateConfig('max_age_days', parseInt(e.target.value))}
              />
            </label>
          </div>

          <div className="config-group">
            <label>
              <span>Batch Size</span>
              <input
                type="number"
                min="1"
                max="50"
                value={config.batch_size}
                onChange={(e) => updateConfig('batch_size', parseInt(e.target.value))}
              />
            </label>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="crystallization-actions">
        <button 
          className="btn-trigger"
          onClick={triggerCrystallization}
          disabled={isTriggering}
        >
          {isTriggering ? '⏳ Triggering...' : '🧊 Trigger Crystallization'}
        </button>
        <button 
          className="btn-refresh"
          onClick={fetchData}
        >
          🔄 Refresh
        </button>
      </div>

      {/* Message */}
      {message && (
        <div className={`crystallization-message ${message.type}`}>
          {message.text}
        </div>
      )}

      {/* Last Run */}
      {stats?.last_run && (
        <div className="crystallization-last-run">
          Last run: {new Date(stats.last_run).toLocaleString()}
        </div>
      )}
    </div>
  );
};
