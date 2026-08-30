import { create } from 'zustand';

export interface MCPTool {
  id: string;
  name: string;
  description: string;
  type: 'server' | 'client';
  status: 'active' | 'inactive' | 'error';
  usageCount: number;
  lastUsed?: number;
}

interface MCPState {
  tools: MCPTool[];
  activeConnections: number;
  addTool: (tool: MCPTool) => void;
  toggleTool: (id: string) => void;
}

export const useMCPStore = create<MCPState>((set) => ({
  tools: [
    { id: '1', name: 'Google Calendar', description: 'Access and manage calendar events', type: 'client', status: 'active', usageCount: 42, lastUsed: Date.now() },
    { id: '2', name: 'Discord', description: 'Post alerts to discord channels', type: 'client', status: 'active', usageCount: 156, lastUsed: Date.now() },
    { id: '3', name: 'Local File System', description: 'Read/write access to studio directory', type: 'server', status: 'active', usageCount: 892, lastUsed: Date.now() },
    { id: '4', name: 'SQLite DB', description: 'Direct query access to Layer 2 data', type: 'server', status: 'active', usageCount: 210, lastUsed: Date.now() },
  ],
  activeConnections: 4,
  addTool: (tool) => set((state) => ({ tools: [...state.tools, tool] })),
  toggleTool: (id) => set((state) => ({
    tools: state.tools.map(t => t.id === id ? { ...t, status: t.status === 'active' ? 'inactive' : 'active' } : t)
  })),
}));
