import { create } from 'zustand';

export interface GovernanceRule {
  id: string;
  name: string;
  description: string;
  type: 'restriction' | 'permission' | 'obligation';
  status: 'active' | 'review' | 'disabled';
}

interface GovernanceState {
  constitution: GovernanceRule[];
  veriLinkStatus: 'verified' | 'unverified' | 'tampered';
  lastRotation: number;
  updateRule: (id: string, updates: Partial<GovernanceRule>) => void;
  rotateKeys: () => void;
}

export const useGovernanceStore = create<GovernanceState>((set) => ({
  constitution: [
    { id: '1', name: 'Identity Sovereignty', description: 'Personal data must never leave the local environment without explicit HITL approval.', type: 'restriction', status: 'active' },
    { id: '2', name: 'Predictive Transparency', description: 'All risk assessments must be accompanied by evidence links to Layer 3 patterns.', type: 'obligation', status: 'active' },
    { id: '3', name: 'External Model Buffer', description: 'PHI data must be tokenized before transmission to cloud inference engines.', type: 'restriction', status: 'active' },
    { id: '4', name: 'Right to Forget', description: 'Automated pattern invalidation upon user deletion request.', type: 'permission', status: 'review' },
  ],
  veriLinkStatus: 'verified',
  lastRotation: Date.now() - 7200000, // 2 hours ago
  updateRule: (id, updates) => set((state) => ({
    constitution: state.constitution.map(r => r.id === id ? { ...r, ...updates } : r)
  })),
  rotateKeys: () => set({ lastRotation: Date.now() }),
}));
