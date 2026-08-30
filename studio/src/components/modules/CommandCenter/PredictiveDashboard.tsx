import React, { useEffect } from 'react';
import { usePredictive } from '../../../hooks/usePredictive';

export const PredictiveDashboard: React.FC = () => {
  const { 
    drift, 
    risks, 
    insights, 
    suggestions, 
    isLoading, 
    fetchAll 
  } = usePredictive();

  useEffect(() => {
    fetchAll();
  }, []);

  if (isLoading) {
    return <div className="predictive-loading">Loading predictive intelligence...</div>;
  }

  return (
    <div className="predictive-dashboard">
      {/* Drift Detection */}
      <div className="predictive-card">
        <h4>📈 Model Drift</h4>
        <div className="drift-metrics">
          <div className="drift-item">
            <span className="drift-label">Overall Drift</span>
            <span className="drift-value">{drift?.overall || 0}%</span>
          </div>
          <div className="drift-item">
            <span className="drift-label">Security Model</span>
            <span className="drift-value">{drift?.security || 0}%</span>
          </div>
          <div className="drift-item">
            <span className="drift-label">Compliance Model</span>
            <span className="drift-value">{drift?.compliance || 0}%</span>
          </div>
        </div>
      </div>

      {/* Risk Assessment */}
      <div className="predictive-card">
        <h4>🎯 Risk Assessment</h4>
        <div className="risk-metrics">
          <div className="risk-item high">
            <span className="risk-label">High Risk</span>
            <span className="risk-count">{risks?.high || 0}</span>
          </div>
          <div className="risk-item medium">
            <span className="risk-label">Medium Risk</span>
            <span className="risk-count">{risks?.medium || 0}</span>
          </div>
          <div className="risk-item low">
            <span className="risk-label">Low Risk</span>
            <span className="risk-count">{risks?.low || 0}</span>
          </div>
        </div>
      </div>

      {/* Insights */}
      <div className="predictive-card insights">
        <h4>💡 Insights</h4>
        <ul className="insights-list">
          {insights?.map((insight, index) => (
            <li key={index} className="insight-item">
              <span className="insight-icon">💡</span>
              <span className="insight-text">{insight.title}</span>
            </li>
          ))}
          {(!insights || insights.length === 0) && (
            <li className="insight-item empty">No insights available</li>
          )}
        </ul>
      </div>

      {/* Suggestions */}
      <div className="predictive-card suggestions">
        <h4>🤖 Suggestions</h4>
        <ul className="suggestions-list">
          {suggestions?.map((suggestion, index) => (
            <li key={index} className="suggestion-item">
              <span className="suggestion-text">{suggestion.title}</span>
              <button className="suggestion-action">Apply</button>
            </li>
          ))}
          {(!suggestions || suggestions.length === 0) && (
            <li className="suggestion-item empty">No suggestions available</li>
          )}
        </ul>
      </div>
    </div>
  );
};
