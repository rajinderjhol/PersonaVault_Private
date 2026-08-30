import { create } from 'zustand';

export interface TraceStep {
  id: string;
  type: 'detection' | 'policy' | 'recommendation' | 'decision' | 'action';
  status: 'pending' | 'active' | 'complete' | 'error';
  label: string;
  details?: string;
  timestamp?: number;
}

export interface DecisionTrace {
  id: string;
  timestamp: number;
  steps: TraceStep[];
  confidence: number;
  evidence: string[];
}

interface TraceState {
  activeTrace: DecisionTrace | null;
  history: DecisionTrace[];
  setActiveTrace: (trace: DecisionTrace | null) => void;
  addTraceToHistory: (trace: DecisionTrace) => void;
}

export const useTraceStore = create<TraceState>((set) => ({
  activeTrace: {
    id: '824',
    timestamp: Date.now(),
    confidence: 0.98,
    evidence: ['Episodic memory #124', 'Security Policy v2.1', 'Signal #942'],
    steps: [
      { id: '1', type: 'detection', status: 'complete', label: 'Signal Detected' },
      { id: '2', type: 'policy', status: 'complete', label: 'Policy Match: SEC-01' },
      { id: '3', type: 'recommendation', status: 'active', label: 'Analyzing Risks' },
      { id: '4', type: 'decision', status: 'pending', label: 'Human Approval Required' },
      { id: '5', type: 'action', status: 'pending', label: 'Execute Action' },
    ]
  },
  history: [],
  setActiveTrace: (trace) => set({ activeTrace: trace }),
  addTraceToHistory: (trace) => set((state) => ({ history: [trace, ...state.history] })),
}));
