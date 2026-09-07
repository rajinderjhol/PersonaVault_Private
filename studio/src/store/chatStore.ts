import { create } from 'zustand';
import { chatAPI } from '../api/chat';
import type { ChatMessage, ChatSession, ChatResponse } from '../api/chat';

interface ChatState {
  // State
  sessions: ChatSession[];
  currentSessionId: string | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  loadSessions: () => Promise<void>;
  createSession: (title?: string) => Promise<ChatSession>;
  loadSession: (sessionId: string) => Promise<void>;
  sendMessage: (query: string, provider?: string) => Promise<ChatResponse>;
  addMessage: (message: ChatMessage) => void;
  pinSession: (sessionId: string) => Promise<void>;
  unpinSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  clearMessages: () => void;
  setCurrentSession: (sessionId: string) => void;
}

// Helper to clean up AI thinking tags
const cleanResponse = (text: string): string => {
  if (!text) return text;
  return text.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
};

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  sessions: [],
  currentSessionId: null,
  messages: [],
  isStreaming: false,
  isLoading: false,
  error: null,

  // Load all sessions
  loadSessions: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await chatAPI.listSessions();
      set({ sessions: data, isLoading: false });
      // Auto-select first session if none selected
      if (data.length > 0 && !get().currentSessionId) {
        await get().loadSession(data[0].id);
      }
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Create a new session
  createSession: async (title: string = 'New Chat') => {
    set({ isLoading: true, error: null });
    try {
      const session = await chatAPI.createSession(title);
      set((state) => ({
        sessions: [session, ...state.sessions],
        currentSessionId: session.id,
        messages: [],
        isLoading: false,
      }));
      return session;
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
      throw error;
    }
  },

  // Load a session's messages
  loadSession: async (sessionId: string) => {
    set({ isLoading: true, error: null });
    try {
      const messages = await chatAPI.getSessionMessages(sessionId);
      set({
        currentSessionId: sessionId,
        messages,
        isLoading: false,
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  // Send a message
  sendMessage: async (query: string, provider: string = 'groq') => {
    const currentSessionId = get().currentSessionId;
    set({ isStreaming: true, error: null });
    console.log('🔍 ChatStore: Sending message...', { query, currentSessionId });

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({
      messages: [...state.messages, userMessage],
    }));

    try {
      const response = await chatAPI.sendMessage(query, currentSessionId || undefined, provider);
      console.log('🔍 ChatStore: API Response received:', response);

      // If we got a session ID back, update current session
      if (response.session_id && !get().currentSessionId) {
        set({ currentSessionId: response.session_id });
        await get().loadSessions();
      }

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: cleanResponse(response.response || response.finalResponse || 'No response'),
        provider: provider,
        trace_ids: response.trace_ids,
        created_at: new Date().toISOString(),
      };
      console.log('🔍 ChatStore: Adding assistant message:', assistantMessage);
      
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isStreaming: false,
      }));

      // Refresh sessions to update message counts
      await get().loadSessions();

      return response;
    } catch (error) {
      console.error('🔍 ChatStore: Error in sendMessage:', error);
      set({ error: (error as Error).message, isStreaming: false });
      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Error: ' + (error as Error).message,
        created_at: new Date().toISOString(),
      };
      set((state) => ({
        messages: [...state.messages, errorMessage],
      }));
      throw error;
    }
  },

  // Add a message manually (for streaming)
  addMessage: (message: ChatMessage) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  // Pin/unpin session
  pinSession: async (sessionId: string) => {
    try {
      await chatAPI.pinSession(sessionId);
      await get().loadSessions();
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  unpinSession: async (sessionId: string) => {
    try {
      await chatAPI.unpinSession(sessionId);
      await get().loadSessions();
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Delete session
  deleteSession: async (sessionId: string) => {
    try {
      await chatAPI.deleteSession(sessionId);
      await get().loadSessions();
      if (get().currentSessionId === sessionId) {
        const sessions = get().sessions;
        if (sessions.length > 0) {
          await get().loadSession(sessions[0].id);
        } else {
          set({ currentSessionId: null, messages: [] });
        }
      }
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Update session title
  updateSessionTitle: async (sessionId: string, title: string) => {
    try {
      await chatAPI.updateSession(sessionId, title);
      await get().loadSessions();
    } catch (error) {
      set({ error: (error as Error).message });
    }
  },

  // Clear current messages
  clearMessages: () => {
    set({ messages: [] });
  },

  // Set current session
  setCurrentSession: (sessionId: string) => {
    set({ currentSessionId: sessionId });
    get().loadSession(sessionId);
  },
}));
