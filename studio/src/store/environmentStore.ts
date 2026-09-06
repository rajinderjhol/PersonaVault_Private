import { create } from 'zustand';
import { v2ApiClient } from '../api/v2Client';

interface Environment {
  id: string;
  name: string;
  type: string;
  ownerPrincipalId: string;
}

// ✅ Add a fallback for when the API fails
const DEFAULT_ENVIRONMENT = {
  id: 'env-default-001',
  name: 'Default Environment',
  type: 'default',
  ownerPrincipalId: 'admin',
};

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
      
      if (!environments || environments.length === 0) {
        console.warn('No environments found, using default');
        set({
          environments: [DEFAULT_ENVIRONMENT],
          currentEnvId: DEFAULT_ENVIRONMENT.id,
          isLoading: false,
        });
        return;
      }
      
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
      
      // ✅ On error, still provide a default environment
      console.warn('Using default environment due to API error');
      set({
        environments: [DEFAULT_ENVIRONMENT],
        currentEnvId: DEFAULT_ENVIRONMENT.id,
        error: (error as Error).message,
        isLoading: false,
      });
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
        ownerPrincipalId: 'user-1', // Placeholder owner
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
