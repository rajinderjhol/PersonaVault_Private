import { create } from 'zustand';

export interface BehaviorPack {
  id: string;
  name: string;
  domain: string;
  version: string;
  status: 'draft' | 'compiled' | 'deployed';
  content: string; // YAML content
}

interface CompilerState {
  packs: BehaviorPack[];
  activePackId: string | null;
  compilationLog: string[];
  isCompiling: boolean;
  addPack: (pack: BehaviorPack) => void;
  updatePack: (id: string, content: string) => void;
  setActivePack: (id: string | null) => void;
  compilePack: (id: string) => void;
}

const DEFAULT_YAML = `pack:
  name: Security Intelligence
  domain: security
  version: "1.0.0"
  
entities:
  - incident
  - alert
  
policies:
  - name: data_loss_prevention
    trigger: outbound_transfer
    action: block_and_notify
    confidence_threshold: 0.85
`;

export const useCompilerStore = create<CompilerState>((set) => ({
  packs: [
    { id: '1', name: 'Security Intelligence', domain: 'security', version: '1.0.0', status: 'compiled', content: DEFAULT_YAML },
    { id: '2', name: 'Robotics Pack', domain: 'robotics', version: '0.9.2', status: 'draft', content: 'pack:\n  name: Robotics\n  domain: robotics...' },
  ],
  activePackId: '1',
  compilationLog: [
    '[12:00:01] Initializing compiler...',
    '[12:00:02] Validating YAML schema...',
    '[12:00:03] Schema valid. Extracting signals...',
    '[12:00:05] Compilation complete: Security Intelligence v1.0.0'
  ],
  isCompiling: false,
  addPack: (pack) => set((state) => ({ packs: [...state.packs, pack] })),
  updatePack: (id, content) => set((state) => ({
    packs: state.packs.map(p => p.id === id ? { ...p, content, status: 'draft' } : p)
  })),
  setActivePack: (id) => set({ activePackId: id }),
  compilePack: (id) => {
    set({ isCompiling: true });
    // Simulate compilation
    setTimeout(() => {
      set((state) => ({
        isCompiling: false,
        compilationLog: [...state.compilationLog, `[${new Date().toLocaleTimeString()}] Compiled ${state.packs.find(p => p.id === id)?.name}`],
        packs: state.packs.map(p => p.id === id ? { ...p, status: 'compiled' } : p)
      }));
    }, 2000);
  },
}));
