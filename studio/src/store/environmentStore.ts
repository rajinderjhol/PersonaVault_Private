import { create } from 'zustand';
import { v2ApiClient } from '../api/v2Client';

interface Environment {
  id: string;
  name: string;
  type: string;
  ownerPrincipalId: string;
}

interface EnvironmentState {
  currentEnvId: string | null;
  environments: Environment[];
  isLoading: boolean;
  error: string | null;
  fetchEnvironments: () => Promise<void>;
  setCurrentEnvironment: (envId: string) => void;
  createEnvironment: (name: string) => Promise<void>;
}

export const useEnvironmentStore = create<EnvironmentState>((set, get) => ({
  currentEnvId: null,
  environments: [],
  isLoading: false,
  error: null,
  fetchEnvironments: async () => {
    console.log('📡 EnvironmentStore: Fetching environments...');
    set({ isLoading: true });
    try {
      const environments = await v2ApiClient.get<Environment[]>('/environments/');
      console.log('✅ EnvironmentStore: Received environments:', environments);
      set({ environments });
      
      // Auto-select logic:
      // 1. If currentEnvId is null, select the first one.
      // 2. If currentEnvId is not null but not in the new list, select the first one.
      const currentExists = environments.some(e => e.id === get().currentEnvId);
      if (!currentExists && environments.length > 0) {
        console.log('🎯 EnvironmentStore: Auto-selecting first environment:', environments[0].id);
        set({ currentEnvId: environments[0].id });
      }
    } catch (error) {
      console.error('❌ EnvironmentStore: Fetch failed:', error);
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },
  setCurrentEnvironment: (envId) => set({ currentEnvId: envId }),
  createEnvironment: async (name: string) => {
    set({ isLoading: true });
    try {
      const newEnv = await v2ApiClient.post<Environment>('/environments/', {
        name,
        owner_principal_id: 'user-1', // Placeholder owner
        type: 'standard'
      });
      await get().fetchEnvironments();
      set({ currentEnvId: newEnv.id });
    } catch (error) {
      set({ error: (error as Error).message });
    } finally {
      set({ isLoading: false });
    }
  },
}));
