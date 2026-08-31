import { create } from 'zustand';
import { mcpAPI, MCPTool, MCPIntegration } from '../api/mcp';

interface MCPState {
  tools: MCPTool[];
  integrations: MCPIntegration[];
  isLoading: boolean;
  error: string | null;
  fetchTools: () => Promise<void>;
  fetchIntegrations: () => Promise<void>;
  callTool: (toolName: string, params: Record<string, any>) => Promise<any>;
  toggleTool: (toolId: string) => void;
}

export const useMCPStore = create<MCPState>((set) => ({
  tools: [],
  integrations: [],
  isLoading: false,
  error: null,

  fetchTools: async () => {
    set({ isLoading: true });
    try {
      const tools = await mcpAPI.listTools();
      set({ tools, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch MCP tools', isLoading: false });
    }
  },

  fetchIntegrations: async () => {
    set({ isLoading: true });
    try {
      const integrations = await mcpAPI.listIntegrations();
      set({ integrations, isLoading: false });
    } catch (error) {
      set({ error: 'Failed to fetch MCP integrations', isLoading: false });
    }
  },

  callTool: async (toolName: string, params: Record<string, any>) => {
    try {
      return await mcpAPI.callTool(toolName, params);
    } catch (error) {
      set({ error: `Failed to call tool ${toolName}` });
      throw error;
    }
  },

  toggleTool: (toolId: string) => {
    console.log('Toggle tool:', toolId);
  },
}));
