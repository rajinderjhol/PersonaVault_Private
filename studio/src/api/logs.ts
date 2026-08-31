import { apiClient } from './client';

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  source: string;
  message: string;
  metadata?: Record<string, any>;
}

export const logsAPI = {
  streamLogs: async (onLog: (log: LogEntry) => void): Promise<() => void> => {
    const data = await apiClient.get<any>('/admin/dashboard/logs/stream', {
      responseType: 'stream',
    });

    const reader = data.getReader();
    const decoder = new TextDecoder();
    let isActive = true;

    const readStream = async () => {
      while (isActive) {
        try {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n').filter(line => line.trim());
          for (const line of lines) {
            try {
              const log = JSON.parse(line);
              onLog(log);
            } catch (e) {
              // Skip non-JSON lines
            }
          }
        } catch (e) {
          break;
        }
      }
    };

    readStream();

    return () => {
      isActive = false;
      reader.cancel();
    };
  },
};
