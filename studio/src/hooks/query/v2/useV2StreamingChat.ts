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
        const response = await fetch(
          `/v2/environments/${currentEnvId}/chat/stream`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify({
              message,
              pack_ids: packIds,
            }),
          }
        );

        if (!response.ok) {
          throw new Error(`Chat failed: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        if (!reader) {
          throw new Error('No response stream available');
        }

        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                onChunk(data);
              } catch (e) {
                console.warn('Failed to parse chunk:', line);
              }
            }
          }
        }

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
