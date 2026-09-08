import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, User, Bot, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { IntelligenceResolutionFeed } from '../../../chat/IntelligenceResolutionFeed';
import { DecisionGate } from '../../../decision/DecisionGate';
import { ActionHub } from '../../../chat/ActionHub';
import { AttributionGroup } from '../../../chat/AttributionGroup';
import { MemoryAttribution } from '../../../chat/MemoryAttribution';
import { DecisionTraceStoryboard } from '../../../decision/DecisionTraceStoryboard';
import { ChatMessage } from '../../../../api/chat';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  currentMessage: ChatMessage | null;
  onSendMessage: (message: string) => void;
  isStreaming: boolean;
  error: string | null;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  currentMessage,
  onSendMessage,
  isStreaming,
  error,
}) => {
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const content = input;
    setInput('');
    onSendMessage(content);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentMessage]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: '20px',
      position: 'relative'
    }}>
      {/* Messages Area */}
      <div 
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '24px',
          paddingRight: '12px'
        }}
      >
        <AnimatePresence>
          {messages.map((msg, index) => (
            <MessageItem key={msg.id || index} message={msg} />
          ))}
          {currentMessage && (
            <MessageItem key="current-message" message={currentMessage} />
          )}
        </AnimatePresence>
        {error && <div style={{ color: 'var(--color-danger)' }}>⚠️ {error}</div>}
      </div>
      
      {/* Input Area */}
      <div style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderRadius: '16px',
        padding: '16px',
        border: '1px solid var(--glass-border)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
      }}>
        <textarea 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask PersonaVault about a decision..."
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--color-text-primary)',
            fontSize: '1rem',
            resize: 'none',
            outline: 'none',
            minHeight: '60px',
            fontFamily: 'inherit'
          }}
        />
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '16px', color: 'var(--color-text-muted)' }}>
            <Paperclip size={20} style={{ cursor: 'pointer' }} />
            <Mic size={20} style={{ cursor: 'pointer' }} />
          </div>
          <button 
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            style={{
              backgroundColor: 'var(--color-gas)',
              color: 'var(--color-bg-primary)',
              border: 'none',
              padding: '8px 20px',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              opacity: (!input.trim() || isStreaming) ? 0.5 : 1
            }}
          >
            Send <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};

const MessageItem: React.FC<{ message: ChatMessage }> = ({ message }) => {
  const isUser = message.role === 'user';
  const [showStoryboard, setShowStoryboard] = useState(false);
  const isStreaming = message.isStreaming || false;
  
  const handleActionClick = async (action: any) => {
    console.log('Action clicked:', action);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '16px',
        alignItems: 'flex-start',
        width: '100%'
      }}
    >
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: '8px',
        backgroundColor: isUser ? 'var(--color-bg-tertiary)' : 'rgba(0, 242, 255, 0.1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: `1px solid ${isUser ? 'var(--glass-border)' : 'rgba(0, 242, 255, 0.2)'}`,
        flexShrink: 0
      }}>
        {isUser ? <User size={20} color="var(--color-text-secondary)" /> : <Bot size={20} color="var(--color-gas)" />}
      </div>
      
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        maxWidth: isUser ? '80%' : '100%',
        flex: 1,
        alignItems: isUser ? 'flex-end' : 'flex-start'
      }}>
        {/* Agent Attribution */}
        {!isUser && message.agentAttribution && (
          <AttributionGroup 
            attributions={message.agentAttribution}
            variant="inline"
          />
        )}

        {/* Intelligence Resolution Feed */}
        {!isUser && message.resolutions && (
          <IntelligenceResolutionFeed resolutions={message.resolutions} />
        )}

        <div style={{
          backgroundColor: isUser ? 'var(--color-bg-secondary)' : 'rgba(15, 23, 42, 0.3)',
          padding: '16px',
          borderRadius: isUser ? '16px 4px 16px 16px' : '4px 16px 16px 16px',
          border: '1px solid var(--glass-border)',
          color: 'var(--color-text-primary)',
          fontSize: '0.95rem',
          lineHeight: 1.5,
          backdropFilter: 'var(--glass-blur)',
          width: isUser ? 'auto' : '100%',
          borderBottom: isStreaming ? '2px solid var(--color-gas)' : 'none',
          transition: 'border-color 0.3s ease',
        }}>
          {message.content}
          {isStreaming && (
            <span style={{
              display: 'inline-block',
              color: 'var(--color-gas)',
              marginLeft: '2px',
              animation: 'blink 0.8s step-end infinite'
            }}>▊</span>
          )}
        </div>
        
        {/* Memory Attribution */}
        {!isUser && message.memoryAttribution && (
          <MemoryAttribution 
            layer={message.memoryAttribution.layer}
            confidence={message.memoryAttribution.confidence}
            source={message.memoryAttribution.source}
          />
        )}
        
        {/* Decision Trace Toggle (The Praesidium inspired storyboard) */}
        {!isUser && (message.trace_ids || message.decision) && (
          <div style={{ width: '100%' }}>
            <button 
              onClick={() => setShowStoryboard(!showStoryboard)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                fontSize: '0.75rem',
                color: 'var(--color-gas)',
                backgroundColor: 'rgba(0, 242, 255, 0.05)',
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid rgba(0, 242, 255, 0.1)',
                cursor: 'pointer',
                marginTop: '4px',
                transition: 'all 0.2s',
                fontWeight: 600
              }}
            >
              <Sparkles size={12} /> 
              {showStoryboard ? 'Hide Decision Storyboard' : 'View Decision Storyboard'}
              {showStoryboard ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            
            <AnimatePresence>
              {showStoryboard && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{ overflow: 'hidden' }}
                >
                  <DecisionTraceStoryboard 
                    trace={message.decision?.timeline || message.trace_ids} 
                    onClose={() => setShowStoryboard(false)}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
        
        {/* Decision Gate */}
        {!isUser && message.decision && !isStreaming && (
          <DecisionGate 
            decision={message.decision}
            onReplay={(id) => console.log('Replay:', id)}
            onDownloadEvidence={(id) => console.log('Download:', id)}
            onCopyId={(id) => console.log('Copy:', id)}
          />
        )}
        
        {/* Streaming Decision Gate Placeholder */}
        {!isUser && message.decision && isStreaming && (
          <div style={{ 
            padding: '8px 16px', 
            background: 'rgba(0, 242, 255, 0.05)',
            borderRadius: '8px',
            fontSize: '0.85rem',
            color: 'var(--color-text-muted)',
            border: '1px dashed rgba(0, 242, 255, 0.2)',
            animation: 'pulse 1.5s ease-in-out infinite'
          }}>
            ⏳ Decision trace being generated...
          </div>
        )}
        
        {/* Action Hub */}
        {!isUser && message.actions && (
          <ActionHub 
            actions={message.actions}
            decisionId={message.decision?.decisionId}
            verdict={message.decision?.verdict}
            onActionClick={handleActionClick}
            isLoading={isStreaming}
          />
        )}
      </div>
    </motion.div>
  );
};
