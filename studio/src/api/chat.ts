import { apiClient } from './client';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  trace_ids?: Record<string, string>;
  created_at: string;
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
  attribution?: {
    phase: string;
    pattern?: string;
  };
  reasoningTrace?: Array<{
    step: number;
    label: string;
    description: string;
  }>;
}

export const chatAPI = {
  // Send a message (non-streaming)
  sendMessage: async (query: string, sessionId?: number, provider?: string): Promise<ChatResponse> => {
    const response = await apiClient.post('/chat/', {
      query,
      session_id: sessionId,
      provider: provider || 'groq',
    });
    return response.data;
  },

  // Stream a message
  streamMessage: async (query: string, sessionId?: number, provider?: string): Promise<ReadableStream> => {
    const response = await apiClient.post('/chat/stream', {
      query,
      session_id: sessionId,
      provider: provider || 'groq',
    }, {
      responseType: 'stream',
    });
    return response.data;
  },

  // List all sessions
  listSessions: async (): Promise<ChatSession[]> => {
    const response = await apiClient.get('/chat/sessions/');
    return response.data || [];
  },

  // Create a new session
  createSession: async (title: string = 'New Chat'): Promise<ChatSession> => {
    const response = await apiClient.post('/chat/sessions/', { title });
    return response.data;
  },

  // Get messages for a session
  getSessionMessages: async (sessionId: number): Promise<ChatMessage[]> => {
    const response = await apiClient.get(`/chat/sessions/${sessionId}/messages`);
    return response.data.messages || [];
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
