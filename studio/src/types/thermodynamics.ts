export interface PhaseDistribution {
  gas: number;
  liquid: number;
  ice: number;
  snowflakes: number;
  total: number;
  timestamp: string;
}

export interface Transition {
  type: string;
  description: string;
  timestamp: string;
}

export interface Snowflake {
  id: string;
  domain: string;
  name: string;
  pattern_count: number;
  confidence: number;
  focus: string[];
}
