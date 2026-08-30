/**
 * Thought Store - Zustand store for real-time thought narrative
 */

import { create } from 'zustand';
import type { ThoughtStep } from '../api/websocket';

interface ThoughtState {
  steps: ThoughtStep[];
  isStreaming: boolean;
  currentStep: ThoughtStep | null;
  error: string | null;
  addStep: (step: ThoughtStep) => void;
  updateStep: (stepIndex: number, step: ThoughtStep) => void;
  clear: () => void;
  setStreaming: (isStreaming: boolean) => void;
  setError: (error: string | null) => void;
}

export const useThoughtStore = create<ThoughtState>((set, get) => ({
  steps: [],
  isStreaming: false,
  currentStep: null,
  error: null,

  addStep: (step: ThoughtStep) => {
    set((state) => ({
      steps: [...state.steps, step],
      currentStep: step,
    }));
  },

  updateStep: (stepIndex: number, step: ThoughtStep) => {
    set((state) => {
      const newSteps = [...state.steps];
      newSteps[stepIndex] = step;
      return { steps: newSteps };
    });
  },

  clear: () => {
    set({ steps: [], currentStep: null });
  },

  setStreaming: (isStreaming: boolean) => {
    set({ isStreaming });
  },

  setError: (error: string | null) => {
    set({ error });
  },
}));
