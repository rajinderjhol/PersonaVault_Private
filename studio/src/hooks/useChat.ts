import { useEffect } from 'react';
import { useChatStore } from '../store/chatStore';

export const useChat = (autoLoad: boolean = true) => {
  const {
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    isLoading,
    error,
    loadSessions,
    createSession,
    loadSession,
    sendMessage,
    addMessage,
    pinSession,
    unpinSession,
    deleteSession,
    updateSessionTitle,
    clearMessages,
    setCurrentSession,
  } = useChatStore();

  // Auto-load sessions on mount
  useEffect(() => {
    if (autoLoad) {
      loadSessions();
    }
  }, [autoLoad]);

  return {
    // Data
    sessions,
    currentSessionId,
    messages,
    isStreaming,
    isLoading,
    error,

    // Actions
    loadSessions,
    createSession,
    loadSession,
    sendMessage,
    addMessage,
    pinSession,
    unpinSession,
    deleteSession,
    updateSessionTitle,
    clearMessages,
    setCurrentSession,
  };
};
