import { api } from './api';

export const mcpService = {
  getServers: () => api.get('/mcp/servers'),
  getClients: () => api.get('/mcp/clients'),
};
