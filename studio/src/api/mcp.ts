import { apiClient } from './client';

export interface MCPTool {
  name: string;
  description: string;
  parameters: Record<string, string>;
  enabled: boolean;
}

export interface MCPIntegration {
  id: string;
  name: string;
  type: 'server' | 'client';
  status: 'connected' | 'disconnected' | 'error';
  tools: MCPTool[];
}

export const mcpAPI = {
  listTools: async (): Promise<MCPTool[]> => {
    const response = await apiClient.get('/mcp/tools');
    return response.data.tools || [];
  },

  callTool: async (toolName: string, params: Record<string, any>): Promise<any> => {
    const response = await apiClient.post(`/mcp/call/${toolName}`, params);
    return response.data;
  },

  listIntegrations: async (): Promise<MCPIntegration[]> => {
    const response = await apiClient.get('/integrations/');
    return response.data || [];
  },
};
