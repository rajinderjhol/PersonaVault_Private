import React, { useState, useEffect } from 'react';
import { useTraces } from '../../../hooks/useTraces';
import { DecisionGraph } from '../../graph/DecisionGraph';

export const DecisionReplay: React.FC = () => {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [replayStep, setReplayStep] = useState(0);
  const [isReplaying, setIsReplaying] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const { recentTraces, fetchRecent, fetchTrace, currentTrace } = useTraces();

  useEffect(() => {
    fetchRecent();
  }, []);

  useEffect(() => {
    if (selectedTraceId) {
      fetchTrace(selectedTraceId);
    }
  }, [selectedTraceId]);

  const handleReplayStart = () => {
    if (currentTrace) {
      setIsReplaying(true);
      setReplayStep(0);
      // Start replay animation
      const interval = setInterval(() => {
        setReplayStep(prev => {
          if (prev >= 4) {
            clearInterval(interval);
            setIsReplaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    }
  };

  const traceSteps = [
    { id: 'perception', label: '🔍 Perception', status: 'complete' },
    { id: 'policy_match', label: '📋 Policy Match', status: 'complete' },
    { id: 'ai_recommendation', label: '🤖 AI Recommendation', status: 'complete' },
    { id: 'action', label: '⚡ Action', status: 'complete' },
    { id: 'outcome', label: '✅ Outcome', status: 'complete' },
  ];

  const getStepStatus = (index: number) => {
    if (!isReplaying && replayStep === 0) return 'pending';
    if (index <= replayStep) return 'complete';
    return 'pending';
  };

  return (
    <div className="decision-replay">
      <div className="replay-header">
        <h3>⏱️ Decision Replay</h3>
        <div className="replay-controls">
          <select 
            value={selectedTraceId || ''}
            onChange={(e) => setSelectedTraceId(e.target.value || null)}
          >
            <option value="">Select a decision to replay...</option>
            {recentTraces.map(trace => (
              <option key={trace.id} value={trace.id}>
                {new Date(trace.timestamp).toLocaleString()} - {trace.step}
              </option>
            ))}
          </select>
          <button 
            onClick={handleReplayStart}
            disabled={!selectedTraceId || isReplaying}
          >
            {isReplaying ? '⏳ Replaying...' : '▶ Replay'}
          </button>
          <button onClick={() => { setReplayStep(0); setIsReplaying(false); }}>
            ⏹ Reset
          </button>
          <button 
            onClick={() => setShowGraph(true)}
            disabled={!selectedTraceId}
          >
            📊 View Provenance Graph
          </button>
        </div>
      </div>

      {showGraph && currentTrace && (
        <div className="graph-modal">
          <div className="modal-content">
            <button onClick={() => setShowGraph(false)}>Close</button>
            <DecisionGraph 
              decisionId={currentTrace.decision_id}
              onNodeClick={(node) => setSelectedNode(node)}
            />
            {selectedNode && (
              <div className="node-detail">
                <h4>Node Details</h4>
                <pre>{JSON.stringify(selectedNode.data, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTraceId && currentTrace && (
        <div className="replay-content">
          <div className="replay-timeline">
            {traceSteps.map((step, index) => (
              <div key={step.id} className={`replay-step ${getStepStatus(index)}`}>
                <span className="step-label">{step.label}</span>
                <span className="step-status">
                  {getStepStatus(index) === 'complete' ? '✅' : '⏳'}
                </span>
                {index < traceSteps.length - 1 && (
                  <div className="step-connector" />
                )}
              </div>
            ))}
          </div>

          <div className="replay-details">
            <div className="replay-data">
              <h4>Decision Data</h4>
              <pre>{JSON.stringify(currentTrace.data, null, 2)}</pre>
            </div>
            <div className="replay-confidence">
              <span>Confidence: {currentTrace.confidence_score * 100}%</span>
              <span>Agent: {currentTrace.agent_id || 'Unknown'}</span>
            </div>
            <button className="crystallize-btn">
              🧊 Crystallize Decision
            </button>
          </div>
        </div>
      )}

      {!selectedTraceId && (
        <div className="replay-empty">
          Select a decision from the list above to start replay.
        </div>
      )}
    </div>
  );
};
