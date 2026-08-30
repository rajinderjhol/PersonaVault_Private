import { create } from 'zustand';

export interface MarketplacePack {
  id: string;
  name: string;
  domain: string;
  description: string;
  version: string;
  author: string;
  rating: number;
  installCount: number;
  isInstalled: boolean;
  metrics?: {
    events: number;
    confidence: number;
    patterns: number;
  };
}

interface MarketplaceState {
  availablePacks: MarketplacePack[];
  activePackId: string | null;
  installPack: (id: string) => void;
  uninstallPack: (id: string) => void;
  setActivePack: (id: string | null) => void;
}

export const useMarketplaceStore = create<MarketplaceState>((set) => ({
  availablePacks: [
    { 
      id: 'sec-01', 
      name: 'Security Intelligence', 
      domain: 'security', 
      description: 'Advanced threat detection and data loss prevention patterns.', 
      version: '1.2.0', 
      author: 'PersonaVault Core',
      rating: 4.9, 
      installCount: 1240, 
      isInstalled: true,
      metrics: { events: 54, confidence: 0.908, patterns: 42 }
    },
    { 
      id: 'rob-01', 
      name: 'Robotics Pack', 
      domain: 'robotics', 
      description: 'Human-robot interaction and safety protocol management.', 
      version: '0.9.5', 
      author: 'PersonaVault Core',
      rating: 4.7, 
      installCount: 840, 
      isInstalled: false 
    },
    { 
      id: 'leg-01', 
      name: 'Legal Compliance', 
      domain: 'legal', 
      description: 'Automated contract analysis and GDPR compliance workflows.', 
      version: '2.1.0', 
      author: 'Legal Swarm Inc',
      rating: 4.8, 
      installCount: 3200, 
      isInstalled: true,
      metrics: { events: 15, confidence: 0.879, patterns: 12 }
    },
    { 
      id: 'med-01', 
      name: 'Clinical Intelligence', 
      domain: 'clinical', 
      description: 'Medical data processing and diagnostic support patterns.', 
      version: '1.0.4', 
      author: 'BioVault',
      rating: 4.6, 
      installCount: 150, 
      isInstalled: false 
    },
  ],
  activePackId: 'sec-01',
  installPack: (id) => set((state) => ({
    availablePacks: state.availablePacks.map(p => p.id === id ? { ...p, isInstalled: true } : p)
  })),
  uninstallPack: (id) => set((state) => ({
    availablePacks: state.availablePacks.map(p => p.id === id ? { ...p, isInstalled: false } : p)
  })),
  setActivePack: (id) => set({ activePackId: id }),
}));
