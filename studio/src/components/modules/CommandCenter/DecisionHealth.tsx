import React, { useEffect, useState, useCallback } from 'react';
import { apiClient } from '../../../api/client';

interface HealthMetric {
  score: number;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  trend: 'improving' | 'declining' | 'stable' | 'unknown';
  details: Record<string, any>;
}

interface HealthData {
  overall: {
    score: number;
    status: string;
    timestamp: string;
  };
  components: {
    confidence: HealthMetric;
    crystallization: HealthMetric;
    traces: HealthMetric;
    system: HealthMetric;
  };
  metrics: {
    step_distribution: Record<string, number>;
    crystallization_rate: any;
  };
}

export const DecisionHealth: React.FC = () => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      const response = await apiClient.get('/health/decision');
      setHealth(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch health data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [fetchHealth]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'critical': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return '✅';
      case 'warning': return '⚠️';
      case 'critical': return '❌';
      default: return '❓';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving': return '📈';
      case 'declining': return '📉';
      default: return '➡️';
    }
  };

  if (isLoading) {
    return <div className="health-loading">Loading health metrics...</div>;
  }

  if (error) {
    return <div className="health-error">Error: {error}</div>;
  }

  if (!health) {
    return <div className="health-empty">No health data available</div>;
  }

  return (
    <div className="decision-health">
      {/* Overall Score */}
      <div className="health-overall">
        <div 
          className="health-gauge"
          style={{ 
            '--score': health.overall.score,
            '--color': getStatusColor(health.overall.status)
          } as React.CSSProperties}
        >
          <svg viewBox="0 0 120 120">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e2e8f0" strokeWidth="10"/>
            <circle 
              cx="60" 
              cy="60" 
              r="50" 
              fill="none" 
              stroke={getStatusColor(health.overall.status)}
              strokeWidth="10"
              strokeDasharray={`${(health.overall.score / 100) * 314} 314`}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
            />
            <text x="60" y="55" textAnchor="middle" fontSize="24" fontWeight="700" fill="#0f172a">
              {Math.round(health.overall.score)}%
            </text>
            <text x="60" y="75" textAnchor="middle" fontSize="10" fill="#94a3b8">
              {health.overall.status}
            </text>
          </svg>
        </div>
        <div className="health-timestamp">
          Updated: {new Date(health.overall.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {/* Components */}
      <div className="health-components">
        {Object.entries(health.components).map(([name, metric]) => (
          <div key={name} className="health-component">
            <div className="component-header">
              <span className="component-name">
                {name.charAt(0).toUpperCase() + name.slice(1)}
              </span>
              <span className="component-status" style={{ color: getStatusColor(metric.status) }}>
                {getStatusIcon(metric.status)} {metric.score}%
              </span>
            </div>
            <div className="component-bar">
              <div 
                className="component-fill"
                style={{ 
                  width: `${metric.score}%`,
                  backgroundColor: getStatusColor(metric.status)
                }}
              />
            </div>
            <div className="component-details">
              <span className="component-trend">
                {getTrendIcon(metric.trend)} {metric.trend}
              </span>
              <span className="component-meta">
                {Object.entries(metric.details || {}).map(([key, value]) => (
                  <span key={key}>{key}: {typeof value === 'number' ? value.toFixed(2) : value}</span>
                ))}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Step Distribution */}
      {health.metrics?.step_distribution && (
        <div className="health-steps">
          <h4>Step Distribution</h4>
          <div className="step-bars">
            {Object.entries(health.metrics.step_distribution).map(([step, count]) => (
              <div key={step} className="step-bar">
                <span className="step-label">{step}</span>
                <div className="step-track">
                  <div 
                    className="step-fill"
                    style={{ 
                      width: `${(count / Math.max(...Object.values(health.metrics.step_distribution))) * 100}%`
                    }}
                  />
                </div>
                <span className="step-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
