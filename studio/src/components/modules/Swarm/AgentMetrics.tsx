import React, { useEffect, useState, useCallback } from 'react';
import { apiClient } from '../../../api/client';

interface AgentMetric {
  agent: string;
  task_count: number;
  success_rate: number;
  avg_latency: number;
  last_active: string;
}

export const AgentMetrics: React.FC = () => {
  const [metrics, setMetrics] = useState<AgentMetric[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchMetrics = useCallback(async () => {
    try {
      const response = await apiClient.get('/swarm/metrics');
      setMetrics(response.data.agents);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000);
    return () => clearInterval(interval);
  }, [fetchMetrics]);

  if (isLoading) {
    return <div className="metrics-loading">Loading metrics...</div>;
  }

  return (
    <div className="agent-metrics">
      <h3>📊 Agent Performance</h3>
      <div className="metrics-grid">
        {metrics.map(metric => (
          <div key={metric.agent} className="metric-card">
            <h4>{metric.agent}</h4>
            <div className="metric-row">
              <span>Tasks</span>
              <span>{metric.task_count}</span>
            </div>
            <div className="metric-row">
              <span>Success Rate</span>
              <span>{metric.success_rate}%</span>
            </div>
            <div className="metric-row">
              <span>Avg Latency</span>
              <span>{metric.avg_latency}ms</span>
            </div>
            <div className="metric-row">
              <span>Last Active</span>
              <span>{new Date(metric.last_active).toLocaleTimeString()}</span>
            </div>
            <div className="metric-bar">
              <div 
                className="metric-fill"
                style={{ 
                  width: `${metric.success_rate}%`,
                  backgroundColor: metric.success_rate > 80 ? '#10b981' : 
                                 metric.success_rate > 50 ? '#f59e0b' : '#ef4444'
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
