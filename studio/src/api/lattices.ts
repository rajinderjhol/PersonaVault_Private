import { apiClient } from './client';

export interface LatticeNode {
  id: string;
  label: string;
  type: 'gas' | 'liquid' | 'ice' | 'snowflake';
  isCrystallized: boolean;
  x: number;
  y: number;
  radius: number;
  color: string;
}

export interface LatticeEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  color: string;
}

export interface LatticeData {
  nodes: LatticeNode[];
  edges: LatticeEdge[];
}

export const latticesAPI = {
  getLattices: async (): Promise<LatticeData> => {
    const response = await apiClient.get('/admin/dashboard/blackboard/snapshot');
    const data = response.data;
    
    // Transform blackboard data into lattice format
    const nodes: LatticeNode[] = [];
    const edges: LatticeEdge[] = [];
    
    // Assuming data is a flat list of nodes and edges from blackboard
    // This part requires mapping your actual API response structure to LatticeNode/Edge
    
    return { nodes, edges };
  },
};
