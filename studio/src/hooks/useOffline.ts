import { useState, useEffect } from 'react';

/**
 * useOffline Hook
 * Detects connectivity and manages an action queue for background sync.
 */

interface QueuedAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
}

export const useOffline = () => {
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [queue, setQueue] = useState<QueuedAction[]>([]);

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const enqueueAction = (type: string, payload: any) => {
    const action: QueuedAction = {
      id: Math.random().toString(36).substring(7),
      type,
      payload,
      timestamp: Date.now(),
    };
    setQueue((prev) => [...prev, action]);
    
    // Persist to localStorage for resilience
    const storedQueue = JSON.parse(localStorage.getItem('pv_sync_queue') || '[]');
    localStorage.setItem('pv_sync_queue', JSON.stringify([...storedQueue, action]));
  };

  const processQueue = async (handler: (action: QueuedAction) => Promise<void>) => {
    if (isOffline) return;

    const currentQueue = [...queue];
    for (const action of currentQueue) {
      try {
        await handler(action);
        setQueue((prev) => prev.filter((a) => a.id !== action.id));
      } catch (error) {
        console.error(`Failed to sync action ${action.id}`, error);
        break; // Stop processing if an error occurs to maintain order
      }
    }
  };

  return { isOffline, queue, enqueueAction, processQueue };
};
