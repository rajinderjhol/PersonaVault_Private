import React from 'react';
import { Search, Bell, LogOut, User } from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { useLocation } from 'react-router-dom';

const CorePanel: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  
  const getBreadcrumb = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/chat') return 'Cognitive Lab';
    if (path === '/search') return 'Universal Search';
    if (path === '/ingestion') return 'Intelligence Vault';
    if (path === '/simulator') return 'Policy Simulator';
    return 'Studio';
  };
  
  return (
    <main style={{
      flex: 1,
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      backgroundColor: 'var(--color-bg-primary)',
      overflow: 'hidden',
      position: 'relative'
    }}>
      {/* Header */}
      <header className="glass-panel" style={{
        height: 'var(--header-height)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderTop: 'none',
        borderLeft: 'none',
        borderRight: 'none',
        zIndex: 5
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>
            <span>Studio</span>
            <span>/</span>
            <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>{getBreadcrumb()}</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            backgroundColor: 'var(--color-bg-secondary)', 
            padding: '6px 12px', 
            borderRadius: '20px',
            border: '1px solid var(--glass-border)'
          }}>
            <Search size={16} color="var(--color-text-muted)" />
            <input 
              type="text" 
              placeholder="Universal Search (Cmd+K)" 
              style={{ 
                background: 'none', 
                border: 'none', 
                color: 'var(--color-text-primary)', 
                marginLeft: '8px',
                fontSize: '0.85rem',
                outline: 'none',
                width: '180px'
              }} 
            />
          </div>
          <Bell size={20} color="var(--color-text-secondary)" />
          
          {/* User/Logout Section */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--color-text-secondary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.85rem' }}>
              <User size={16} />
              {user?.username || 'User'}
            </div>
            <button 
              onClick={logout}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center' }}
              title="Logout"
            >
              <LogOut size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', position: 'relative' }}>
        {children}
      </div>

      {/* Footer Status Bar */}
      <footer style={{
        height: 'var(--footer-height)',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.75rem',
        color: 'var(--color-text-muted)',
        borderTop: '1px solid var(--glass-border)',
        backgroundColor: 'var(--color-bg-secondary)'
      }}>
        <div style={{ display: 'flex', gap: '20px' }}>
          <span>Provider: <span style={{ color: 'var(--color-gas)' }}>Groq / Llama 3</span></span>
          <span>Mode: <span style={{ color: 'var(--color-liquid)' }}>Sovereign</span></span>
        </div>
        <div style={{ display: 'flex', gap: '20px' }}>
          <span>Latency: 42ms</span>
          <span>Confidence: 98%</span>
        </div>
      </footer>
    </main>
  );
};

export default CorePanel;
