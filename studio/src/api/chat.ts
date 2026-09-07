import { apiClient } from './client';

export interface IntelligenceResolution {
  packId: string;
  packName: string;
  memories: {
    layer: 1 | 2 | 3;
    count: number;
    summary?: string;
  }[];
  policies: {
    count: number;
    matched?: string[];
  };
}

export interface DecisionGate {
  decisionId: string;
  verdict: 'APPROVED' | 'CONTAINED' | 'ESCALATED' | 'REFUSED';
  reasonCode: string;
  summary: string;
  consensus: {
    total: number;
    agreed: number;
  };
  timeline: {
    perception: any;
    policyMatch: any;
    aiRecommendation: any;
    decisionMade: any;
    provenanceLogged: any;
  };
  evidenceId?: string;
  timestamp: string;
}

export interface SuggestedAction {
  id: string;
  label: string;
  description?: string;
  icon?: string;
  action: string;
  payload?: any;
  primary?: boolean;
}

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  thought?: string;
  provider?: string;
  timestamp?: string;
  created_at?: string;
  trace_ids?: Record<string, string>;
  resolutions?: IntelligenceResolution[];
  decision?: DecisionGate;
  actions?: SuggestedAction[];
  isStreaming?: boolean;
  agentAttribution?: {
    agentId: string;
    agentName: string;
    packId: string;
    packName: string;
  }[];
}

export interface ChatSession {
  id: number;
  title: string;
  pinned: boolean;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ChatResponse {
  response: string;
  finalResponse?: string;
  session_id?: number;
  trace_ids?: Record<string, string>;
  attribution?: IntelligenceResolution[];
  decision?: DecisionGate;
  actions?: SuggestedAction[];
  reasoningTrace?: Array<{
    step: number;
    label: string;
    description: string;
  }>;
}

export const chatAPI = {
  // ... rest of the file remains unchanged

  sendMessage: async (query: string, sessionId?: number, provider?: string): Promise<ChatResponse> => {
    return await apiClient.post('/chat', {
      query,
      session_id: sessionId,
      provider: provider || 'groq',
    });
  },

  // Stream a message
  streamMessage: async (query: string, sessionId?: number, provider?: string): Promise<ReadableStream> => {
    return await apiClient.post('/chat/stream', {
      query,
      session_id: sessionId,
      provider: provider || 'groq',
    }, {
      responseType: 'stream',
    });
  },

  // List all sessions
  listSessions: async (): Promise<ChatSession[]> => {
    const data = await apiClient.get<ChatSession[]>('/chat/sessions/');
    return data || [];
  },

  // Create a new session
  createSession: async (title: string = 'New Chat'): Promise<ChatSession> => {
    return await apiClient.post('/chat/sessions/', { title });
  },

  // Get messages for a session
  getSessionMessages: async (sessionId: number): Promise<ChatMessage[]> => {
    const data = await apiClient.get<any>(`/chat/sessions/${sessionId}/messages`);
    return data.messages || [];
  },

  // Pin/unpin session
  pinSession: async (sessionId: number): Promise<void> => {
    await apiClient.patch(`/chat/sessions/${sessionId}/pin`);
  },

  unpinSession: async (sessionId: number): Promise<void> => {
    await apiClient.patch(`/chat/sessions/${sessionId}/unpin`);
  },

  // Delete session
  deleteSession: async (sessionId: number): Promise<void> => {
    await apiClient.delete(`/chat/sessions/${sessionId}`);
  },

  // Update session title
  updateSession: async (sessionId: number, title: string): Promise<void> => {
    await apiClient.patch(`/chat/sessions/${sessionId}`, { title });
  },
};
