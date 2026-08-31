import { useQuery } from '@tanstack/react-query';
import { mcpService } from '../../services/mcpService';

export const useMCPQuery = () => {
  return useQuery({
    queryKey: ['mcp-data'],
    queryFn: async () => {
      const [servers, clients] = await Promise.all([
        mcpService.getServers(),
        mcpService.getClients(),
      ]);
      return { servers, clients };
    },
    staleTime: 60000,
  });
};
