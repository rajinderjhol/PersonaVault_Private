import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../api/client';
import { Clock, Calendar, TrendingUp, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface TimingAnalysis {
  urgency: string;
  deadline: string;
  optimal_time: string;
  recommendation: {
    status: string;
    suggestion: string;
    best_slot: { start: string; end: string } | null;
    alternatives: { start: string; end: string }[];
  };
}

interface DecisionTimePattern {
  hour: number;
  count: number;
  confidence: number;
}

export const TemporalInsights: React.FC = () => {
  const [analysis, setAnalysis] = useState<TimingAnalysis | null>(null);
  const [patterns, setPatterns] = useState<DecisionTimePattern[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [urgencyFilter, setUrgencyFilter] = useState('all');

  useEffect(() => {
    fetchTemporalData();
  }, []);

  const fetchTemporalData = async () => {
    try {
      const [analysisRes, patternsRes] = await Promise.all([
        apiClient.get('/mcp/temporal/analyze-decision-timing'),
        apiClient.get('/mcp/temporal/decision-patterns')
      ]);
      setAnalysis(analysisRes.data);
      setPatterns(patternsRes.data || []);
    } catch (error) {
      console.error('Failed to fetch temporal data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'critical': return '#ef4444';
      case 'high': return '#f97316';
      case 'medium': return '#f59e0b';
      default: return '#94a3b8';
    }
  };

  const getUrgencyEmoji = (urgency: string) => {
    switch (urgency) {
      case 'critical': return '🚨';
      case 'high': return '🔴';
      case 'medium': return '🟡';
      default: return '🟢';
    }
  };

  if (isLoading) {
    return <div className="temporal-loading">Analyzing temporal intelligence...</div>;
  }

  return (
    <div className="temporal-insights">
      <div className="temporal-header">
        <h3>🕐 Temporal Intelligence</h3>
        <div className="time-display">
          <Clock size={16} />
          <span>{new Date().toLocaleString()}</span>
        </div>
      </div>

      {/* Urgency Filter */}
      <div className="urgency-filters">
        <button 
          className={urgencyFilter === 'all' ? 'active' : ''}
          onClick={() => setUrgencyFilter('all')}
        >
          All
        </button>
        <button 
          className={urgencyFilter === 'critical' ? 'active critical' : ''}
          onClick={() => setUrgencyFilter('critical')}
        >
          🚨 Critical
        </button>
        <button 
          className={urgencyFilter === 'high' ? 'active high' : ''}
          onClick={() => setUrgencyFilter('high')}
        >
          🔴 High
        </button>
        <button 
          className={urgencyFilter === 'medium' ? 'active medium' : ''}
          onClick={() => setUrgencyFilter('medium')}
        >
          🟡 Medium
        </button>
        <button 
          className={urgencyFilter === 'low' ? 'active low' : ''}
          onClick={() => setUrgencyFilter('low')}
        >
          🟢 Low
        </button>
      </div>

      {/* Timing Analysis */}
      {analysis && (
        <div className="analysis-section">
          <h4>Decision Timing Analysis</h4>
          <div className="analysis-grid">
            <div className="analysis-card urgency">
              <span className="analysis-label">Urgency</span>
              <span 
                className="analysis-value"
                style={{ color: getUrgencyColor(analysis.urgency) }}
              >
                {getUrgencyEmoji(analysis.urgency)} {analysis.urgency}
              </span>
            </div>
            <div className="analysis-card deadline">
              <span className="analysis-label">Deadline</span>
              <span className="analysis-value">
                {new Date(analysis.deadline).toLocaleString()}
              </span>
            </div>
            <div className="analysis-card optimal">
              <span className="analysis-label">Optimal Time</span>
              <span className="analysis-value">
                {new Date(analysis.optimal_time).toLocaleString()}
              </span>
            </div>
            <div className="analysis-card recommendation">
              <span className="analysis-label">Recommendation</span>
              <span className="analysis-value">
                {analysis.recommendation.suggestion}
              </span>
            </div>
          </div>

          {/* Available Slots */}
          {analysis.recommendation.best_slot && (
            <div className="slots-section">
              <h4>Recommended Time Slot</h4>
              <div className="best-slot">
                <Calendar size={16} />
                <span>
                  {new Date(analysis.recommendation.best_slot.start).toLocaleString()} - 
                  {new Date(analysis.recommendation.best_slot.end).toLocaleString()}
                </span>
                <button className="btn-schedule">Schedule Now</button>
              </div>
              {analysis.recommendation.alternatives && (
                <div className="alternative-slots">
                  <span className="slots-label">Alternative slots:</span>
                  {analysis.recommendation.alternatives.map((slot, index) => (
                    <span key={index} className="alt-slot">
                      {new Date(slot.start).toLocaleString().split(',')[1]}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Decision Time Patterns */}
      <div className="patterns-section">
        <h4>Decision Time Patterns</h4>
        <div className="patterns-chart">
          {patterns.map((pattern) => (
            <div key={pattern.hour} className="pattern-bar">
              <div 
                className="pattern-fill"
                style={{
                  height: `${(pattern.count / Math.max(...patterns.map(p => p.count))) * 100}%`,
                  backgroundColor: pattern.confidence > 0.7 ? '#10b981' : 
                                  pattern.confidence > 0.5 ? '#f59e0b' : '#94a3b8'
                }}
              />
              <span className="pattern-label">{pattern.hour}:00</span>
            </div>
          ))}
        </div>
        <div className="patterns-legend">
          <span className="legend-item">
            <span className="legend-dot high"></span> High Confidence (&gt; 70%)
          </span>
          <span className="legend-item">
            <span className="legend-dot medium"></span> Medium Confidence (50-70%)
          </span>
          <span className="legend-item">
            <span className="legend-dot low"></span> Low Confidence ({'< '}50%)
          </span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="temporal-actions">
        <button className="action-btn" onClick={fetchTemporalData}>
          <RefreshCw size={16} /> Refresh Analysis
        </button>
        <button className="action-btn primary">
          <Calendar size={16} /> Schedule All Pending
        </button>
      </div>
    </div>
  );
};
