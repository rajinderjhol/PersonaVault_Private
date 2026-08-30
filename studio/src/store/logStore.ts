import { create } from 'zustand';
import { logsAPI, LogEntry } from '../api/logs';

interface LogState {
  logs: LogEntry[];
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  streamCanceller: (() => void) | null;
  startStream: () => Promise<void>;
  stopStream: () => void;
  clearLogs: () => void;
  addLog: (log: LogEntry) => void;
}

export const useLogStore = create<LogState>((set, get) => ({
  logs: [],
  isStreaming: false,
  isLoading: false,
  error: null,
  streamCanceller: null,

  startStream: async () => {
    set({ isLoading: true, error: null });
    try {
      const canceller = await logsAPI.streamLogs((log) => {
        get().addLog(log);
      });
      set({ 
        isStreaming: true, 
        isLoading: false,
        streamCanceller: canceller 
      });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  stopStream: () => {
    const { streamCanceller } = get();
    if (streamCanceller) {
      streamCanceller();
    }
    set({ isStreaming: false, streamCanceller: null });
  },

  clearLogs: () => {
    set({ logs: [] });
  },

  addLog: (log: LogEntry) => {
    set(state => ({
      logs: [...state.logs, log].slice(-1000), // Keep last 1000 logs
    }));
  },
}));
