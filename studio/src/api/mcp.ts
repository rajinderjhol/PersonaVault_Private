import { apiClient } from './client';

export interface MCPTool {
  id: string;
  name: string;
  description: string;
  parameters: Record<string, string>;
  enabled: boolean;
  type: 'server' | 'client';
  status: 'active' | 'inactive';
  usageCount: number;
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
    const data = await apiClient.get<any>('/mcp/tools');
    return data.tools || [];
  },

  callTool: async (toolName: string, params: Record<string, any>): Promise<any> => {
    return await apiClient.post(`/mcp/call/${toolName}`, params);
  },

  listIntegrations: async (): Promise<MCPIntegration[]> => {
    const data = await apiClient.get<MCPIntegration[]>('/integrations/');
    return data || [];
  },
};
