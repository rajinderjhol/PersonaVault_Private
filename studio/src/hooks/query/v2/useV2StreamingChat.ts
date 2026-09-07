import { useState, useCallback } from 'react';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

interface StreamingChunk {
  type: 'text' | 'intelligence' | 'decision' | 'action' | 'agent' | 'memory' | 'done';
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
      onComplete: (finalData: any) => void
    ) => {
      if (!currentEnvId) {
        setError('No environment selected');
        return;
      }

      setIsStreaming(true);
      setError(null);

      try {
        const url = `/v2/environments/${currentEnvId}/chat/stream?t=${Date.now()}`;
        console.log('📡 V2 Super Power Stream URL (Cache-busted):', url);
        
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message,
            pack_ids: packIds,
            show_reasoning: true
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`V2 Chat failed: ${response.statusText}`);
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        let accumulatedData: any = {
          content: '',
          memoryAttribution: null,
          trace_ids: null,
          decision: null,
          actions: null,
          attribution: null
        };

        if (!reader) throw new Error('Response body is null');

        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep the last partial line in buffer

          for (const line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('data: ')) {
              try {
                const event = JSON.parse(trimmedLine.slice(6));
                console.log('📡 V2 Stream Event:', event);

                switch (event.type) {
                  case 'content':
                    accumulatedData.content += event.content;
                    onChunk({ type: 'text', data: event.content });
                    break;
                  case 'memory':
                    accumulatedData.memoryAttribution = event.data;
                    onChunk({ type: 'memory', data: event.data });
                    break;
                  case 'trace':
                    accumulatedData.trace_ids = event.trace;
                    onChunk({ type: 'decision', data: event.trace });
                    break;
                  case 'status':
                    console.log('📡 System Status:', event.message);
                    break;
                  case 'done':
                    onComplete(accumulatedData);
                    break;
                }
              } catch (e) {
                console.warn('Failed to parse SSE event:', trimmedLine, e);
              }
            }
          }
        }
      } catch (err) {
        console.error('V2 Chat Error:', err);
        setError(err instanceof Error ? err.message : 'V2 Chat failed');
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
