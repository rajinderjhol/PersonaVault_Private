/**
 * Intelligence Source Types - V2 Studio
 * Matches backend Pydantic models in intelligence_sources.py
 */

export interface TrustScoreHistory {
  timestamp: string;
  score: number;
  reason: string;
}

export interface ContributionMetrics {
  patterns_crystallized: number;
  reasoning_steps_validated: number;
  memory_matches_contributed: number;
  decision_traces_triggered: number;
  events_ingested: number;
}

export interface IntelligenceSource {
  id: string;
  name: string;
  type: 'endpoint' | 'iot' | 'agent' | 'behavior_pack';
  trust_score: number;
  trust_level: 'FULL' | 'HIGH' | 'MEDIUM' | 'BASIC' | 'UNTRUSTED';
  trust_history: TrustScoreHistory[];
  contribution_metrics: ContributionMetrics;
  memory_access: string[];
  status: 'active' | 'idle' | 'degraded' | 'offline';
  last_contribution: string | null;
  registered_at: string;
  extra_metadata: Record<string, any>;
}

export interface RegisterSourceRequest {
  name: string;
  type: string;
  initial_trust_level: string;
  memory_access: string[];
  purpose?: string;
}

export interface UpdateSourceRequest {
  name?: string;
  trust_level?: string;
  memory_access?: string[];
  status?: string;
  extra_metadata?: Record<string, any>;
}

export interface LiveFeedEvent {
  source_id: string;
  source_name: string;
  timestamp: string;
  event_type: 'ingestion' | 'trust_change' | 'alert' | 'registration' | 'update';
  message: string;
  details: Record<string, any>;
}

export interface TrustLevelConfig {
  value: number;
  label: string;
  access: string[];
  color: string;
}

export interface SourceStats {
  active_sources: number;
  total_sources: number;
  average_trust_score: number;
  total_contributions: number;
  total_ingestions: number;
}
