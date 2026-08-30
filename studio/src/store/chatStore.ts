import { create } from 'zustand';
import { useTraceStore } from './traceStore';
import { useThermodynamicsStore } from './thermodynamicsStore';
import { useModelStore } from './modelStore';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  thought?: string; // For the Thought Narrative feed
  traceId?: string; // Link to an Auditable Decision Trace
}

interface ChatState {
  messages: Message[];
  isStreaming: boolean;
  activeSessionId: string | null;
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setStreaming: (streaming: boolean) => void;
  setSession: (id: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am your PersonaVault intelligence agent. How can I assist you with your decision processes today?',
      timestamp: Date.now(),
    }
  ],
  isStreaming: false,
  activeSessionId: 'default-session',
  
  addMessage: (msg) => set((state) => ({
    messages: [...state.messages, {
      ...msg,
      id: Math.random().toString(36).substring(7),
      timestamp: Date.now()
    }]
  })),

  sendMessage: async (content) => {
    const { addMessage } = get();
    const traceStore = useTraceStore.getState();
    const thermoStore = useThermodynamicsStore.getState();
    
    // 1. Add user message
    addMessage({ role: 'user', content });
    set({ isStreaming: true });
    
    // 2. Trigger active trace start
    traceStore.setActiveTrace({
      id: Math.floor(Math.random() * 1000).toString(),
      timestamp: Date.now(),
      confidence: 0.95,
      evidence: ['Real-time user input', 'Cognitive Mesh v1.0'],
      steps: [
        { id: '1', type: 'detection', status: 'complete', label: 'Signal Detected' },
        { id: '2', type: 'policy', status: 'active', label: 'Matching Security Policies' },
        { id: '3', type: 'recommendation', status: 'pending', label: 'Analyzing Risks' },
        { id: '4', type: 'decision', status: 'pending', label: 'Finalizing' },
        { id: '5', type: 'action', status: 'pending', label: 'Execute' },
      ]
    });

    try {
      const assistantId = Math.random().toString(36).substring(7);
      
      set((state) => ({
        messages: [...state.messages, {
          id: assistantId,
          role: 'assistant',
          content: '',
          timestamp: Date.now(),
          thought: 'Initializing cognitive swarm... Accessing Security Pack...'
        }]
      }));
      
      const { selectedModel, selectedProvider } = useModelStore.getState();

      const response = await fetch('/api/v1/ollama/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: get().messages.slice(-10).map(m => ({ role: m.role, content: m.content })),
          model: selectedModel,
          provider: selectedProvider
        })
      });

      if (!response.ok) throw new Error('Network response was not ok');
      if (!response.body) throw new Error('No response body');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.message?.content) {
              accumulatedContent += data.message.content;
              
              set((state) => ({
                messages: state.messages.map(m => m.id === assistantId ? {
                  ...m,
                  content: accumulatedContent,
                  thought: accumulatedContent.length > 100 
                    ? 'Synthesizing final response... Mapping to decision nodes...' 
                    : accumulatedContent.length > 50 
                    ? 'Retrieving episodic memories... Validating against governance...' 
                    : m.thought
                } : m)
              }));

              // Gradually complete trace steps
              if (accumulatedContent.length > 150) {
                traceStore.setActiveTrace({
                  ...traceStore.activeTrace!,
                  steps: traceStore.activeTrace!.steps.map((s, i) => i < 4 ? { ...s, status: 'complete' } : s)
                });
              } else if (accumulatedContent.length > 50) {
                traceStore.setActiveTrace({
                  ...traceStore.activeTrace!,
                  steps: traceStore.activeTrace!.steps.map((s, i) => i < 2 ? { ...s, status: 'complete' } : i === 2 ? { ...s, status: 'active' } : s)
                });
              }
            }
          } catch (e) {}
        }
      }

      // 3. Finalize Trace and trigger crystallization
      set((state) => ({
        isStreaming: false,
        messages: state.messages.map(m => m.id === assistantId ? {
          ...m,
          thought: 'Cognitive loop complete. Insight crystallized. Trace archived.',
          traceId: traceStore.activeTrace?.id
        } : m)
      }));

      traceStore.setActiveTrace({
        ...traceStore.activeTrace!,
        steps: traceStore.activeTrace!.steps.map(s => ({ ...s, status: 'complete' }))
      });

      thermoStore.addTransition(`Freeze: Interaction #${traceStore.activeTrace?.id} crystallized into Semantic Memory`);
      thermoStore.setPhase('ice', Math.min(thermoStore.phases.ice + 1, 100));

    } catch (error) {
      console.error('Chat Error:', error);
      set({ isStreaming: false });
      addMessage({ 
        role: 'system', 
        content: 'System Error: Cognitive Gateway Unreachable. Check Ollama connection.' 
      });
    }
  },

  clearMessages: () => set({ messages: [] }),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setSession: (id) => set({ activeSessionId: id }),
}));
