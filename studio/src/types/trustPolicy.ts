/**
 * Trust Policy Types - V2 Studio
 * Matches backend Pydantic models in trust_policies.py
 */

export interface TrustPolicy {
  id: string;
  layer: 'gas' | 'liquid' | 'ice' | 'crystallized';
  min_trust_threshold: number;
  max_trust_threshold: number | null;
  is_enforced: boolean;
  action_on_violation: 'block' | 'warn' | 'quarantine';
  notification_enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface TrustPolicyCreateRequest {
  layer: string;
  min_trust_threshold?: number;
  max_trust_threshold?: number | null;
  action_on_violation?: string;
  notification_enabled?: boolean;
}

export interface TrustPolicyUpdateRequest {
  min_trust_threshold?: number;
  max_trust_threshold?: number | null;
  is_enforced?: boolean;
  action_on_violation?: string;
  notification_enabled?: boolean;
}

export interface DefaultPolicyConfig {
  min_trust_threshold: number;
  recommended_action: string;
}

export interface SimulationResult {
  source_id: string;
  source_name: string;
  trust_score: number;
  layer: string;
  current_threshold: number;
  new_threshold: number;
  currently_restricted: boolean;
  would_be_restricted: boolean;
  impact: 'restricted' | 'unrestricted';
  summary: string;
}

export const LAYER_LABELS: Record<string, string> = {
  gas: 'Gas (Working Memory)',
  liquid: 'Liquid (Episodic Memory)',
  ice: 'Ice (Semantic Memory)',
  crystallized: 'Crystallized (Patterns)',
};

export const LAYER_COLORS: Record<string, string> = {
  gas: 'gray',
  liquid: 'cyan',
  ice: 'blue',
  crystallized: 'purple',
};

export const ACTION_LABELS: Record<string, string> = {
  block: '🚫 Block',
  warn: '⚠️ Warn',
  quarantine: '📦 Quarantine',
};

export const ACTION_COLORS: Record<string, string> = {
  block: 'red',
  warn: 'orange',
  quarantine: 'yellow',
};
