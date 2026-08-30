/**
 * Thought Narrative - Real-time agent reasoning stream
 * Displays each thought step as it happens with auto-scroll
 */

import React, { useEffect, useRef, useState } from 'react';
import { useThoughtStore } from '../../../store/thoughtStore';
import { useWebSocket } from '../../../hooks/useWebSocket';
import type { ThoughtStep } from '../../../types/thought';
import '../../styles/thought-narrative.css';

interface ThoughtNarrativeProps {
  isActive?: boolean;
  onThoughtComplete?: (steps: ThoughtStep[]) => void;
}

export const ThoughtNarrative: React.FC<ThoughtNarrativeProps> = ({
  isActive = true,
  onThoughtComplete,
}) => {
  const { steps, isStreaming, error, addStep, setStreaming, setError, clear } = useThoughtStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [isExpanded, setIsExpanded] = useState(true);

  // WebSocket connection for real-time thought stream
  const { isConnected } = useWebSocket({
    onThought: (step: ThoughtStep) => {
      console.log('🧠 Thought received:', step);
      addStep(step);
      setStreaming(step.status !== 'complete');
    },
    onError: (err) => {
      setError(err);
    },
    autoConnect: true,
  });

  // Auto-scroll to bottom when new steps arrive
  useEffect(() => {
    if (containerRef.current && isExpanded) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [steps, isExpanded]);

  // Clear thoughts when chat resets
  useEffect(() => {
    if (!isActive) {
      clear();
    }
  }, [isActive]);

  // Mark streaming complete when done
  useEffect(() => {
    if (steps.length > 0 && !isStreaming) {
      onThoughtComplete?.(steps);
    }
  }, [steps, isStreaming]);

  if (!isActive && steps.length === 0) {
    return (
      <div className="thought-narrative idle">
        <span className="idle-icon">🧠</span>
        <span className="idle-text">Standby for cognitive stream...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="thought-narrative error">
        <span className="error-icon">⚠️</span>
        <span className="error-text">Cognitive stream error: {error}</span>
        <button onClick={() => setError(null)} className="error-dismiss">✕</button>
      </div>
    );
  }

  return (
    <div className="thought-narrative-wrapper">
      <div className="narrative-header">
        <span className="narrative-title">🧠 Thought Narrative</span>
        <div className="narrative-controls">
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '● Live' : '○ Connecting...'}
          </span>
          <button 
            className="toggle-expand"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? '▼' : '▶'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="thought-narrative" ref={containerRef}>
          {steps.length === 0 && !isStreaming && (
            <div className="thought-placeholder">
              <span className="placeholder-icon">💡</span>
              <span>Waiting for cognitive processing...</span>
            </div>
          )}

          {steps.map((step, index) => (
            <div key={index} className={`thought-step ${step.status}`}>
              <div className="step-indicator">
                <span className={`step-dot ${step.status}`} />
                <span className="step-number">{index + 1}</span>
              </div>
              <div className="step-content">
                <div className="step-header">
                  <span className="step-label">{step.label}</span>
                  <span className={`step-status ${step.status}`}>
                    {step.status === 'pending' && '⏳'}
                    {step.status === 'in_progress' && '🔄'}
                    {step.status === 'complete' && '✅'}
                  </span>
                </div>
                <div className="step-description">{step.description}</div>
                {step.timestamp && (
                  <div className="step-timestamp">
                    {new Date(step.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isStreaming && steps.length > 0 && (
            <div className="streaming-indicator">
              <span className="streaming-dot">●</span>
              <span className="streaming-text">Processing...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
