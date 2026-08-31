import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../../../api/client';

interface Prediction {
  type: string;
  domain: string;
  confidence: number;
  prediction: string;
  suggested_action: string;
  urgency: 'high' | 'medium' | 'low';
}

interface Simulation {
  pattern_id: string;
  domain: string;
  confidence: number;
  simulation: {
    success_probability: number;
    risk_level: string;
    expected_impact: {
      efficiency_gain: number;
      risk_reduction: number;
    };
  };
}

interface AutomatedResponse {
  query: string;
  response: string;
  confidence: number;
  times_asked: number;
  ready: boolean;
}

interface Trend {
  confidence_trend: string;
  current_confidence: number;
  crystallization_rate: number;
  total_decisions: number;
  crystallized_patterns: number;
}

export const PredictiveInsights: React.FC = () => {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [simulations, setSimulations] = useState<Simulation[]>([]);
  const [automatedResponses, setAutomatedResponses] = useState<AutomatedResponse[]>([]);
  const [trends, setTrends] = useState<Trend | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('predictions');

  const fetchAllPredictiveData = useCallback(async () => {
    try {
      const [predictionsRes, trendsRes, responsesRes] = await Promise.all([
        apiClient.get('/predictive/predictions'),
        apiClient.get('/predictive/trends'),
        apiClient.get('/predictive/automated-responses')
      ]);
      
      setPredictions(predictionsRes.data.pattern_predictions || []);
      setSimulations(predictionsRes.data.outcome_simulations || []);
      setTrends(trendsRes.data || null);
      setAutomatedResponses(responsesRes.data.responses || []);
    } catch (error) {
      console.error('Failed to fetch predictive data:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllPredictiveData();
    const interval = setInterval(fetchAllPredictiveData, 60000);
    return () => clearInterval(interval);
  }, [fetchAllPredictiveData]);

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return '#ef4444';
      case 'medium': return '#f59e0b';
      default: return '#94a3b8';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#10b981';
      case 'medium': return '#f59e0b';
      case 'high': return '#ef4444';
      default: return '#94a3b8';
    }
  };

  if (isLoading) {
    return <div className="predictive-loading">Loading predictive intelligence...</div>;
  }

  return (
    <div className="predictive-insights">
      {/* Header */}
      <div className="predictive-header">
        <h2>🔮 Predictive Intelligence</h2>
        <div className="predictive-tabs">
          <button 
            className={activeTab === 'predictions' ? 'active' : ''}
            onClick={() => setActiveTab('predictions')}
          >
            Predictions
          </button>
          <button 
            className={activeTab === 'simulations' ? 'active' : ''}
            onClick={() => setActiveTab('simulations')}
          >
            Simulations
          </button>
          <button 
            className={activeTab === 'automated' ? 'active' : ''}
            onClick={() => setActiveTab('automated')}
          >
            Automated Responses
          </button>
          <button 
            className={activeTab === 'trends' ? 'active' : ''}
            onClick={() => setActiveTab('trends')}
          >
            Trends
          </button>
        </div>
      </div>

      {/* Predictions Tab */}
      {activeTab === 'predictions' && (
        <div className="predictions-tab">
          {predictions.length === 0 ? (
            <div className="predictions-empty">
              <span className="empty-icon">🔮</span>
              <p>No predictions yet. Continue making decisions to generate insights.</p>
            </div>
          ) : (
            predictions.map((prediction, index) => (
              <div key={index} className={`prediction-card ${prediction.urgency}`}>
                <div className="prediction-header">
                  <span className="prediction-domain">{prediction.domain}</span>
                  <span 
                    className="prediction-urgency"
                    style={{ backgroundColor: getUrgencyColor(prediction.urgency) }}
                  >
                    {prediction.urgency}
                  </span>
                  <span className="prediction-confidence">{Math.round(prediction.confidence * 100)}%</span>
                </div>
                <div className="prediction-text">{prediction.prediction}</div>
                <div className="prediction-action">
                  <button className="btn-action">{prediction.suggested_action}</button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Simulations Tab */}
      {activeTab === 'simulations' && (
        <div className="simulations-tab">
          {simulations.length === 0 ? (
            <div className="simulations-empty">
              <span className="empty-icon">🎯</span>
              <p>No simulations available. Crystallize patterns to see outcomes.</p>
            </div>
          ) : (
            simulations.map((sim, index) => (
              <div key={index} className="simulation-card">
                <div className="simulation-header">
                  <span className="simulation-domain">{sim.domain}</span>
                  <span 
                    className="simulation-risk"
                    style={{ color: getRiskColor(sim.simulation.risk_level) }}
                  >
                    {sim.simulation.risk_level} risk
                  </span>
                  <span className="simulation-confidence">
                    {Math.round(sim.simulation.success_probability * 100)}% success
                  </span>
                </div>
                <div className="simulation-impact">
                  <div className="impact-item">
                    <span className="impact-label">Efficiency Gain</span>
                    <span className="impact-value">+{Math.round(sim.simulation.expected_impact.efficiency_gain * 100)}%</span>
                  </div>
                  <div className="impact-item">
                    <span className="impact-label">Risk Reduction</span>
                    <span className="impact-value">-{Math.round(sim.simulation.expected_impact.risk_reduction * 100)}%</span>
                  </div>
                </div>
                <button className="btn-simulate">Apply Pattern</button>
              </div>
            ))
          )}
        </div>
      )}

      {/* Automated Responses Tab */}
      {activeTab === 'automated' && (
        <div className="automated-tab">
          {automatedResponses.length === 0 ? (
            <div className="automated-empty">
              <span className="empty-icon">⚡</span>
              <p>No automated responses ready. Common patterns will appear here.</p>
            </div>
          ) : (
            automatedResponses.map((response, index) => (
              <div key={index} className="automated-card">
                <div className="automated-query">"{response.query}"</div>
                <div className="automated-response">{response.response}</div>
                <div className="automated-meta">
                  <span className="meta-confidence">{Math.round(response.confidence * 100)}% confidence</span>
                  <span className="meta-count">Asked {response.times_asked} times</span>
                  <span className="meta-ready">{response.ready ? '✅ Ready' : '⏳ Preparing'}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'trends' && trends && (
        <div className="trends-tab">
          <div className="trends-grid">
            <div className="trend-card">
              <span className="trend-label">Confidence Trend</span>
              <span className={`trend-value ${trends.confidence_trend}`}>
                {trends.confidence_trend === 'improving' ? '📈' : '➡️'} {trends.current_confidence}%
              </span>
            </div>
            <div className="trend-card">
              <span className="trend-label">Crystallization Rate</span>
              <span className="trend-value">{trends.crystallization_rate}%</span>
            </div>
            <div className="trend-card">
              <span className="trend-label">Total Decisions</span>
              <span className="trend-value">{trends.total_decisions}</span>
            </div>
            <div className="trend-card">
              <span className="trend-label">Crystallized Patterns</span>
              <span className="trend-value">{trends.crystallized_patterns}</span>
            </div>
          </div>
          <div className="trend-chart">
            <div className="chart-placeholder">
              <span className="chart-label">Confidence over time</span>
              <div className="chart-bars">
                <div className="chart-bar" style={{ height: '60%' }} />
                <div className="chart-bar" style={{ height: '70%' }} />
                <div className="chart-bar" style={{ height: '80%' }} />
                <div className="chart-bar" style={{ height: '75%' }} />
                <div className="chart-bar" style={{ height: '85%' }} />
                <div className="chart-bar" style={{ height: '90%' }} />
                <div className="chart-bar" style={{ height: '95%' }} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
