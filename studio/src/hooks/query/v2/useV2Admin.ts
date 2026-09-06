import { useQuery, useMutation } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  uptime: string;
  memory: { used: number; total: number; percentage: number };
  cpu: { usage: number; cores: number };
  services: { name: string; status: string; version?: string }[];
  websocket: { connections: number; status: string };
  mode: 'standard' | 'restricted' | 'simulation' | 'audit';
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  source?: string;
  details?: Record<string, any>;
}

export const useV2SystemHealth = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'admin', 'health', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<SystemHealth>(`/environments/${currentEnvId}/admin/health`);
    },
    enabled: !!currentEnvId,
    refetchInterval: 10000,
  });
};

export const useV2ExecutionMode = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (mode: 'standard' | 'restricted' | 'simulation' | 'audit') => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.post(`/environments/${currentEnvId}/admin/mode`, { mode });
    },
  });
};

export const useV2Logs = (options?: { limit?: number; level?: string }) => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'admin', 'logs', currentEnvId, options],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<LogEntry[]>(`/environments/${currentEnvId}/admin/logs`, { params: options });
    },
    enabled: !!currentEnvId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
};
