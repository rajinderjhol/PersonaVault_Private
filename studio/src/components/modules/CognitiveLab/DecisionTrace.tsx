/**
 * Decision Trace - Live 5-step Auditable Decision Trace
 * Visualizes the ADT pipeline in real-time with status updates
 */

import React, { useEffect, useState } from 'react';
import { useThoughtStore } from '../../../store/thoughtStore';

interface TraceStep {
  id: string;
  label: string;
  icon: string;
  status: 'pending' | 'in_progress' | 'complete' | 'error';
  description?: string;
}

const TRACE_STEPS: TraceStep[] = [
  { id: 'perception', label: 'Perception', icon: '🔍', status: 'pending' },
  { id: 'policy_match', label: 'Policy Match', icon: '📋', status: 'pending' },
  { id: 'ai_recommendation', label: 'AI Recommendation', icon: '🤖', status: 'pending' },
  { id: 'action', label: 'Action', icon: '⚡', status: 'pending' },
  { id: 'outcome', label: 'Outcome', icon: '✅', status: 'pending' },
];

interface DecisionTraceProps {
  onTraceComplete?: (trace: any) => void;
}

export const DecisionTrace: React.FC<DecisionTraceProps> = ({ onTraceComplete }) => {
  const { steps } = useThoughtStore();
  const [traceSteps, setTraceSteps] = useState<TraceStep[]>(TRACE_STEPS);
  const [isActive, setIsActive] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<string[]>([]);

  // Map thought steps to trace status
  useEffect(() => {
    if (steps.length === 0) {
      setIsActive(false);
      setTraceSteps(TRACE_STEPS.map(s => ({ ...s, status: 'pending' })));
      setCompletedSteps([]);
      return;
    }

    setIsActive(true);

    // Update trace steps based on thought narrative
    const updatedSteps = traceSteps.map((step) => {
      // Check if this step has been completed in the thought narrative
      const thoughtMatch = steps.find((s) => 
        s.label.toLowerCase().includes(step.label.toLowerCase()) ||
        step.label.toLowerCase().includes(s.label.toLowerCase())
      );

      if (thoughtMatch) {
        const newStatus = thoughtMatch.status === 'in_progress' ? 'in_progress' : 'complete';
        return { ...step, status: newStatus, description: thoughtMatch.description };
      }

      // If previous step is complete, this one is pending
      const prevStepIndex = traceSteps.findIndex(s => s.id === step.id) - 1;
      if (prevStepIndex >= 0) {
        const prevStep = traceSteps[prevStepIndex];
        if (prevStep.status === 'complete' && step.status === 'pending') {
          return { ...step, status: 'pending' };
        }
      }

      return step;
    });

    setTraceSteps(updatedSteps);

    // Check if all steps are complete
    const allComplete = updatedSteps.every(s => s.status === 'complete');
    if (allComplete && completedSteps.length === 0) {
      setCompletedSteps(updatedSteps.map(s => s.id));
      onTraceComplete?.(updatedSteps);
    }
  }, [steps]);

  const getStepStatusIcon = (status: string) => {
    switch (status) {
      case 'complete': return '✅';
      case 'in_progress': return '⏳';
      case 'error': return '❌';
      default: return '○';
    }
  };

  const getStepStatusClass = (status: string) => {
    switch (status) {
      case 'complete': return 'complete';
      case 'in_progress': return 'in-progress';
      case 'error': return 'error';
      default: return 'pending';
    }
  };

  return (
    <div className={`decision-trace ${isActive ? 'active' : 'idle'}`}>
      <div className="trace-header">
        <span className="trace-title">🔍 Decision Trace</span>
        {isActive && <span className="trace-status live">● Live</span>}
      </div>

      <div className="trace-pipeline">
        {traceSteps.map((step, index) => (
          <React.Fragment key={step.id}>
            <div className={`trace-step ${getStepStatusClass(step.status)}`}>
              <div className="step-icon">{step.icon}</div>
              <div className="step-content">
                <div className="step-label">
                  {step.label}
                  <span className="step-status-icon">{getStepStatusIcon(step.status)}</span>
                </div>
                {step.description && (
                  <div className="step-description">{step.description}</div>
                )}
                {step.status === 'in_progress' && (
                  <div className="step-progress">
                    <span className="progress-dot">●</span>
                    <span className="progress-text">Processing...</span>
                  </div>
                )}
              </div>
            </div>

            {index < traceSteps.length - 1 && (
              <div className={`trace-connector ${step.status === 'complete' ? 'complete' : ''}`}>
                <span className="connector-line" />
                <span className="connector-arrow">→</span>
              </div>
            )}
          </React.Fragment>
        ))}
      </div>

      {isActive && (
        <div className="trace-footer">
          <span className="trace-confidence">
            Confidence: {steps.length > 0 ? '85%' : '—'}
          </span>
          <span className="trace-timestamp">
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      )}
    </div>
  );
};
