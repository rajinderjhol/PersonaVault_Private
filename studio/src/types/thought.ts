/**
 * Thought Stream Types
 */

export interface ThoughtStep {
  step: number;
  label: string;
  description: string;
  status: 'pending' | 'in_progress' | 'complete';
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ThoughtStream {
  id: string;
  session_id: string;
  steps: ThoughtStep[];
  started_at: string;
  completed_at?: string;
  total_duration?: number;
}

export interface ThoughtMessage {
  type: 'thought' | 'trace' | 'decision' | 'phase_transition' | 'error';
  data: ThoughtStep | any;
  timestamp: string;
}
