import React, { useState, useEffect } from 'react';
import { useV2StreamingChat } from '../../../hooks/query/v2/useV2StreamingChat';
import { useV2Agents, Agent } from '../../../hooks/query/v2/useV2Agents';
import { useV2Thermodynamics } from '../../../hooks/query/v2/useV2Thermodynamics';
import { useV2Health } from '../../../hooks/query/v2/useV2Health';
import { useV2Insights } from '../../../hooks/query/v2/useV2Insights';
import { useV2GrowthMetrics } from '../../../hooks/query/v2/useV2GrowthMetrics';
import { useAgentWebSocket } from '../../../hooks/websocket/useAgentWebSocket';
import { useStudioStore } from '../../../store/studioStore';
import { useEnvironmentStore } from '../../../store/environmentStore';
import { ChatInterface } from './Chat/ChatInterface';
import { SearchBar } from '../../chat/SearchBar';
import { TemporalContextControls, TemporalContext } from '../../chat/TemporalContextControls';
import { IntelligenceHealth } from '../../dashboard/IntelligenceHealth';
import { IntelligenceInsights } from './Insights/IntelligenceInsights';
import { IntelligenceGrowth } from '../../dashboard/IntelligenceGrowth';
import { AgentSwarmUI } from '../../chat/AgentSwarmUI';
import { AuthButton } from '@/components/Auth/AuthButton';
import { ChatMessage } from '../../../api/chat';
import styles from './CognitiveLab.module.css';

const CognitiveLab: React.FC = () => {
  const { sendMessage, isStreaming, error } = useV2StreamingChat();
  
  // V2 Data Hooks
  const { data: agents, isLoading: agentsLoading } = useV2Agents();
  const { data: thermodynamics, isLoading: thermoLoading } = useV2Thermodynamics();
  const { data: health, isLoading: healthLoading } = useV2Health();
  const { data: insights, isLoading: insightsLoading } = useV2Insights();
  const { data: growth, isLoading: growthLoading } = useV2GrowthMetrics();
  
  // WebSocket for real-time updates
  const { agents: wsAgents, isConnected } = useAgentWebSocket();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState<ChatMessage | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [temporalContext, setTemporalContext] = useState<TemporalContext | null>(null);
  const activePackIds = useStudioStore((state) => state.activePackIds);

  const { environments, currentEnvId, fetchEnvironments } = useEnvironmentStore();
  
  console.log("DEBUG: CognitiveLab render. currentEnvId:", currentEnvId, "environments:", environments);

  useEffect(() => {
    console.log("DEBUG: CognitiveLab effect. environments.length:", environments.length);
    if (environments.length === 0) {
      fetchEnvironments();
    }
  }, [environments.length, fetchEnvironments]);

  // Sync agents from API and WebSocket
  const [activeAgents, setActiveAgents] = useState<Agent[]>([]);

  useEffect(() => {
    const combinedAgents = [...(agents || [])];
    
    wsAgents.forEach(wsAgent => {
      const index = combinedAgents.findIndex(a => a.id === wsAgent.agentId);
      if (index >= 0) {
        combinedAgents[index] = { 
          ...combinedAgents[index], 
          status: wsAgent.status as any,
          lastActivity: wsAgent.lastActivity 
        };
      } else {
        combinedAgents.push({
          id: wsAgent.agentId,
          name: wsAgent.name || wsAgent.agentId,
          status: wsAgent.status as any,
          lastActivity: wsAgent.lastActivity
        } as Agent);
      }
    });

    setActiveAgents(combinedAgents);
  }, [agents, wsAgents]);

  const handleSendMessage = async (message: string) => {
    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: '',
      isStreaming: true,
      timestamp: new Date().toISOString(),
    };
    setCurrentMessage(assistantMessage);

    await sendMessage(
      message,
      activePackIds,
      (chunk) => {
        setCurrentMessage((prev) => {
          if (!prev) return prev;
          const updated = { ...prev };
          switch (chunk.type) {
            case 'text':
              updated.content += chunk.data;
              break;
            case 'intelligence':
              updated.resolutions = [...(updated.resolutions || []), chunk.data];
              break;
            case 'decision':
              updated.decision = chunk.data;
              break;
            case 'action':
              updated.actions = [...(updated.actions || []), chunk.data];
              break;
            case 'agent':
              updated.agentAttribution = [...(updated.agentAttribution || []), chunk.data];
              break;
            case 'memory':
              updated.memoryAttribution = chunk.data;
              break;
          }
          return updated;
        });
      },
      (finalData) => {
        // Construct the final message from the completed data
        const finalContent = finalData.finalResponse || finalData.response || 'No response';
        const finalMessage: ChatMessage = {
          role: 'assistant',
          content: finalContent,
          isStreaming: false,
          timestamp: new Date().toISOString(),
          memoryAttribution: finalData.memoryAttribution,
          resolutions: finalData.attribution,
          decision: finalData.decision,
          actions: finalData.actions,
          trace_ids: finalData.trace_ids
        };

        setMessages(prev => [...prev, finalMessage]);
        setCurrentMessage(null);
      }
    );
  };

  // Handle search
  const handleSearch = (query: string) => {
    setSearchQuery(query);
    console.log('Searching for:', query);
  };

  // Handle temporal context change
  const handleTemporalChange = (context: TemporalContext) => {
    setTemporalContext(context);
    console.log('Temporal context changed:', context);
  };

  // Environment check
  if (!currentEnvId) {
    return (
      <div className={styles.noEnvironment}>
        <div className={styles.emptyState}>
          <span className={styles.icon}>🌍</span>
          <h3>No Environment Selected</h3>
          <p>Please select an environment from the Command Bar or create a new one to start using the Decision Cockpit</p>
          <button 
            onClick={() => fetchEnvironments()}
            style={{
              padding: '10px 20px',
              backgroundColor: 'rgba(0, 242, 255, 0.2)',
              color: 'var(--color-gas, #00f2ff)',
              border: '1px solid var(--color-gas, #00f2ff)',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 600,
              marginTop: '20px',
              transition: 'all 0.2s'
            }}
          >
            Refresh Environments
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.cockpitContainer}>
      {/* Main Chat Area */}
      <div className={styles.mainContent}>
        <div className={styles.chatHeader}>
          <div className={styles.headerLeft}>
            <span className={styles.headerIcon}>🎯</span>
            <span className={styles.headerTitle}>Decision Cockpit</span>
            <span className={`${styles.liveIndicator} ${isConnected ? styles.live : ''}`}>
              {isConnected ? '● LIVE' : '● CONNECTING'}
            </span>
          </div>
          
          <div className={styles.headerCenter}>
            <SearchBar 
              onSearch={handleSearch}
              placeholder="Search decisions, policies, memories..."
            />
          </div>
          
          <div className={styles.headerRight}>
            <AuthButton />
            <span className={styles.statItem}>
              <span className={styles.statLabel}>Agents:</span>
              <span className={styles.statValue}>
                {agentsLoading ? '...' : activeAgents.filter(a => a.status === 'active').length}
              </span>
            </span>
            <span className={styles.statItem}>
              <span className={styles.statLabel}>Memory:</span>
              <span className={styles.statValue}>
                {thermoLoading ? '...' : thermodynamics?.total || 0}
              </span>
            </span>
            <span className={styles.headerStatus}>
              {isStreaming ? '⏳ Processing...' : '✅ Ready'}
            </span>
          </div>
        </div>

        <ChatInterface
          messages={messages}
          currentMessage={currentMessage}
          onSendMessage={handleSendMessage}
          isStreaming={isStreaming}
          error={error}
        />
      </div>

      {/* Enhanced Sidebar */}
      <div className={styles.sidebar}>
        {/* Temporal Context */}
        <div className={styles.sidebarSection}>
          <TemporalContextControls 
            onContextChange={handleTemporalChange}
          />
        </div>

        {/* System Health */}
        <div className={styles.sidebarSection}>
          <IntelligenceHealth 
            health={health}
            isLoading={healthLoading}
          />
        </div>

        {/* Agent Swarm */}
        <div className={styles.sidebarSection}>
          <AgentSwarmUI 
            agents={activeAgents}
            thermodynamics={thermodynamics}
            isLoading={agentsLoading || thermoLoading}
            isActive={isConnected}
          />
        </div>

        {/* Proactive Insights */}
        <div className={styles.sidebarSection}>
          <IntelligenceInsights 
            insights={insights}
            isLoading={insightsLoading}
          />
        </div>

        {/* Intelligence Growth */}
        <div className={styles.sidebarSection}>
          <IntelligenceGrowth 
            data={growth}
            isLoading={growthLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default CognitiveLab;
