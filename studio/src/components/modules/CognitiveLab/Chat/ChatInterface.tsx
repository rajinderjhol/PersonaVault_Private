import React, { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, Mic, User, Bot, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { IntelligenceResolutionFeed } from '../../../chat/IntelligenceResolutionFeed';
import { DecisionGate } from '../../../decision/DecisionGate';
import { ActionHub } from '../../../chat/ActionHub';
import { AttributionGroup } from '../../../chat/AttributionGroup';
import { MemoryAttribution } from '../../../chat/MemoryAttribution';
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
            <MessageItem key={index} message={msg} />
          ))}
          {currentMessage && (
            <MessageItem key="current" message={currentMessage} />
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

const MessageItem: React.FC<{ message: any }> = ({ message }) => {
  const isUser = message.role === 'user';
  
  const handleActionClick = async (action: any) => {
    console.log('Action clicked:', action);
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: '16px',
        alignItems: 'flex-start'
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
        maxWidth: '80%',
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
          backdropFilter: 'var(--glass-blur)'
        }}>
          {message.content}
        </div>
        
        {/* Memory Attribution */}
        {!isUser && message.memoryAttribution && (
          <MemoryAttribution 
            layer={message.memoryAttribution.layer}
            confidence={message.memoryAttribution.confidence}
            source={message.memoryAttribution.source}
          />
        )}
        
        {/* Decision Gate */}
        {!isUser && message.decision && (
          <DecisionGate 
            decision={message.decision}
            onReplay={(id) => console.log('Replay:', id)}
            onDownloadEvidence={(id) => console.log('Download:', id)}
            onCopyId={(id) => console.log('Copy:', id)}
          />
        )}
        
        {/* Action Hub */}
        {!isUser && message.actions && (
          <ActionHub 
            actions={message.actions}
            decisionId={message.decision?.decisionId}
            verdict={message.decision?.verdict}
            onActionClick={handleActionClick}
            isLoading={message.isStreaming}
          />
        )}
        
        {!isUser && message.trace_ids && !message.decision && !message.actions && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '0.75rem',
            color: 'var(--color-gas)',
            backgroundColor: 'rgba(0, 242, 255, 0.05)',
            padding: '4px 8px',
            borderRadius: '4px',
            border: '1px solid rgba(0, 242, 255, 0.1)',
            cursor: 'pointer'
          }}>
            <Sparkles size={12} /> View Decision Trace
          </div>
        )}
      </div>
    </motion.div>
  );
};
