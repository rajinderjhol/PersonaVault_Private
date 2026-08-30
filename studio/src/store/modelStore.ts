import { create } from 'zustand';
import axios from 'axios';

export interface AIModel {
  model_name: string;
  provider_type: string;
  description: string;
}

interface ModelState {
  models: AIModel[];
  selectedProvider: string;
  selectedModel: string;
  isLoading: boolean;
  fetchModels: () => Promise<void>;
  setSelectedProvider: (provider: string) => void;
  setSelectedModel: (model: string) => void;
}

export const useModelStore = create<ModelState>((set, get) => ({
  models: [],
  selectedProvider: 'ollama',
  selectedModel: 'llama3',
  isLoading: false,

  fetchModels: async () => {
    set({ isLoading: true });
    try {
      const response = await axios.get('/api/v1/admin/models');
      console.log('API Response Models:', response.data);
      set({ models: response.data, isLoading: false });
      
      // Auto-select first model if none selected
      if (response.data.length > 0 && !get().selectedModel) {
        set({ selectedModel: response.data[0].id });
      }
    } catch (err) {
      console.error('Failed to fetch models:', err);
      set({ isLoading: false });
    }
  },

  setSelectedProvider: (provider) => set({ selectedProvider: provider }),
  setSelectedModel: (model) => set({ selectedModel: model }),
}));
