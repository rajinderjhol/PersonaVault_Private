import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../../../store/chatStore';
import type { Message } from '../../../../store/chatStore';
import { Send, Paperclip, Mic, User, Bot, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const ChatInterface: React.FC = () => {
  const { messages, sendMessage, isStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const content = input;
    setInput('');
    await sendMessage(content);
  };

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      gap: '20px'
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
          {messages.map((msg) => (
            <MessageItem key={msg.id} message={msg} />
          ))}
        </AnimatePresence>
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

const MessageItem: React.FC<{ message: Message }> = ({ message }) => {
  const isUser = message.role === 'user';
  
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
        
        {!isUser && message.traceId && (
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
            <Sparkles size={12} /> View Decision Trace #{message.traceId}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default ChatInterface;
