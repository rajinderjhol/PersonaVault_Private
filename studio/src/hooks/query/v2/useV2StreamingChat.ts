import { useState, useCallback } from 'react';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

interface StreamingChunk {
  type: 'text' | 'intelligence' | 'decision' | 'action' | 'agent' | 'done';
  data: any;
}

export const useV2StreamingChat = () => {
  const { currentEnvId } = useEnvironmentStore();
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (
      message: string,
      packIds: string[],
      onChunk: (chunk: StreamingChunk) => void,
      onComplete: () => void
    ) => {
      if (!currentEnvId) {
        setError('No environment selected');
        return;
      }

      setIsStreaming(true);
      setError(null);

      try {
        const token = localStorage.getItem('token') || '';
        const url = `/api/v1/chat/`;
        console.log('📡 Chat Requesting (Non-streaming):', url);
        const response = await fetch(
          url,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              query: message,
              provider: 'auto',
              user_id: 1,
            }),
            credentials: 'include',
          }
        );

        if (!response.ok) {
          throw new Error(`Chat failed: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Simulate streaming by returning the whole response as one chunk
        const responseText = data.finalResponse || data.response || 'No response';
        onChunk({ type: 'text', data: responseText });
        
        onComplete();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Chat failed');
      } finally {
        setIsStreaming(false);
      }
    },
    [currentEnvId]
  );

  return {
    sendMessage,
    isStreaming,
    error,
  };
};
