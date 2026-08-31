export interface AgentStatus {
  id: string;
  agentName: string;
  agentType?: string;
  content: string;
  timestamp: string;
  status: 'thinking' | 'active' | 'completed' | 'error';
  confidence?: number;
  temporalContext?: {
    startDate: string;
    endDate: string;
    intervalType: string;
    originalExpression?: string;
    daysSpan?: number;
  };
}
