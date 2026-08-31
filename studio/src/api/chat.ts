import { apiClient } from './client';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  thought?: string;
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
    return await apiClient.post('/chat/', {
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
