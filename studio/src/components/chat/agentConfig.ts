interface AgentConfig {
  id: string;
  name: string;
  packId: string;
  packName: string;
  icon: string;
  color: string;
  bgColor: string;
  description: string;
}

export const AGENT_CONFIG: Record<string, AgentConfig> = {
  'security_agent': {
    id: 'security_agent',
    name: 'Security Agent',
    packId: 'security',
    packName: 'Security Intelligence',
    icon: '🛡️',
    color: '#4A90D9',
    bgColor: '#e8f0fe',
    description: 'Reviews security policies and threats',
  },
  'compliance_agent': {
    id: 'compliance_agent',
    name: 'Compliance Agent',
    packId: 'compliance',
    packName: 'Compliance Intelligence',
    icon: '⚖️',
    color: '#27AE60',
    bgColor: '#e8f5e9',
    description: 'Ensures regulatory compliance',
  },
  'contracts_agent': {
    id: 'contracts_agent',
    name: 'Contracts Agent',
    packId: 'contracts',
    packName: 'Contract Intelligence',
    icon: '📜',
    color: '#9B59B6',
    bgColor: '#f3e5f5',
    description: 'Analyzes contract terms and obligations',
  },
  'procurement_agent': {
    id: 'procurement_agent',
    name: 'Procurement Agent',
    packId: 'procurement',
    packName: 'Procurement Intelligence',
    icon: '📦',
    color: '#F39C12',
    bgColor: '#fff3e0',
    description: 'Manages supply chain and procurement',
  },
  'insurance_agent': {
    id: 'insurance_agent',
    name: 'Insurance Agent',
    packId: 'insurance',
    packName: 'Insurance Intelligence',
    icon: '🛡️',
    color: '#E74C3C',
    bgColor: '#fbe9e7',
    description: 'Reviews insurance policies and claims',
  },
  'robotics_agent': {
    id: 'robotics_agent',
    name: 'Robotics Agent',
    packId: 'robotics',
    packName: 'Robotics Intelligence',
    icon: '🤖',
    color: '#1ABC9C',
    bgColor: '#e0f7fa',
    description: 'Manages robotics and HRI decisions',
  },
};
