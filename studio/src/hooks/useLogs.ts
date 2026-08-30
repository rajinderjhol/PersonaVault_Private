import { useEffect } from 'react';
import { useLogStore } from '../store/logStore';

export const useLogs = (autoStart: boolean = true) => {
  const {
    logs,
    isStreaming,
    isLoading,
    error,
    startStream,
    stopStream,
    clearLogs,
  } = useLogStore();

  useEffect(() => {
    if (autoStart) {
      startStream();
    }
    return () => {
      stopStream();
    };
  }, [autoStart]);

  return {
    logs,
    isStreaming,
    isLoading,
    error,
    startStream,
    stopStream,
    clearLogs,
  };
};
