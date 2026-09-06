import { useMutation, useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface SimulationParams {
  policyId: string;
  scenario: string;
  parameters: Record<string, any>;
}

export interface SimulationResult {
  id: string;
  status: 'running' | 'completed' | 'failed';
  before: {
    confidence: number;
    risk: number;
    cost: number;
    decisions: number;
  };
  after: {
    confidence: number;
    risk: number;
    cost: number;
    decisions: number;
  };
  summary: string;
  recommendations: string[];
  timestamp: string;
}

export const useV2RunSimulation = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useMutation({
    mutationFn: async (params: SimulationParams) => {
      if (!currentEnvId) throw new Error('No environment selected');
      // The router in simulation.py handles /v2/environments/{env_id}/simulations/run
      return await v2ApiClient.post<SimulationResult>(
        `/environments/${currentEnvId}/simulations/run`,
        params
      );
    },
  });
};

export const useV2SimulationStatus = (simulationId: string | null) => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'simulation', 'status', simulationId],
    queryFn: async () => {
      if (!currentEnvId || !simulationId) throw new Error('No simulation ID');
      return v2ApiClient.get<SimulationResult>(
        `/environments/${currentEnvId}/simulations/${simulationId}/status`
      );
    },
    enabled: !!simulationId && !!currentEnvId,
    refetchInterval: 2000, // Poll every 2 seconds
  });
};

export const useV2SimulationHistory = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'simulation', 'history', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<SimulationResult[]>(
        `/environments/${currentEnvId}/simulations/history`
      );
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
  });
};
