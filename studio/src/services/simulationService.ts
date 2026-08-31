import { apiClient } from '../api/client';

export const simulationApi = {
  runSimulation: (domain: string, params: object, startDate: string, endDate: string) => 
    apiClient.post('/simulation/policy', { 
      domain, 
      params, 
      start_date: startDate, 
      end_date: endDate 
    }),
};
