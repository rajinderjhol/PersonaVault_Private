import React from 'react';
import { 
  LayoutDashboard, 
  Database, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  MessageSquare,
  ShieldCheck,
  Cpu,
  Terminal,
  Layers,
  ShoppingBag,
  ShieldAlert,
  Server,
  Calendar,
  Smartphone,
  Search
} from 'lucide-react';
import { create } from 'zustand';
import { Link, useLocation } from 'react-router-dom';

// UI State Store for Navigation
interface NavigationState {
  collapsed: boolean;
  toggleCollapsed: () => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  collapsed: false,
  toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed })),
}));

const LeftPanel: React.FC = () => {
  const { collapsed, toggleCollapsed } = useNavigationStore();
  const location = useLocation();
  const activePath = location.pathname;

  return (
    <aside className="glass-panel" style={{
      width: collapsed ? 'var(--left-panel-collapsed-width)' : 'var(--left-panel-width)',
      height: '100vh',
      borderRight: '1px solid var(--glass-border)',
      transition: 'width var(--transition-speed) ease',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      zIndex: 10,
      borderTop: 'none',
      borderBottom: 'none',
      borderLeft: 'none'
    }}>
      <div style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: collapsed ? 'center' : 'space-between' }}>
        {!collapsed && <h2 style={{ margin: 0, fontSize: '1.2rem', color: 'var(--color-gas)' }}>PersonaVault</h2>}
        <button 
          onClick={toggleCollapsed}
          style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer' }}
        >
          {collapsed ? <ChevronRight size={20} /> : <ChevronLeft size={20} />}
        </button>
      </div>

      <nav style={{ flex: 1, padding: '10px', overflowY: 'auto' }}>
        <NavItem 
          to="/universal-search"
          icon={<Search size={20} />} 
          label="Universal Search" 
          collapsed={collapsed} 
          active={activePath === '/universal-search'} 
        />
        <NavItem 
          to="/admin-tools"
          icon={<Terminal size={20} />} 
          label="Admin Tools" 
          collapsed={collapsed} 
          active={activePath === '/admin-tools'} 
        />
        <NavItem 
          to="/"
          icon={<LayoutDashboard size={20} />} 
          label="Dashboard" 
          collapsed={collapsed} 
          active={activePath === '/'} 
        />
        <NavItem 
          to="/chat" 
          icon={<MessageSquare size={20} />} 
          label="Cognitive Lab" 
          collapsed={collapsed} 
          active={activePath === '/chat'} 
        />
        <NavItem 
          to="/models" 
          icon={<Cpu size={20} />} 
          label="Model Management" 
          collapsed={collapsed} 
          active={activePath === '/models'} 
        />
        <NavItem 
          to="/intelligence-vault" 
          icon={<Database size={20} />} 
          label="Intelligence Vault" 
          collapsed={collapsed} 
          active={activePath === '/intelligence-vault'} 
        />
        <NavItem 
          to="/simulator"
          icon={<Cpu size={20} />} 
          label="Policy Simulator" 
          collapsed={collapsed} 
          active={activePath === '/simulator'} 
        />
        
        <div style={{ height: '1px', backgroundColor: 'var(--glass-border)', margin: '10px 0' }} />
        
        <NavItem 
          to="/marketplace"
          icon={<ShoppingBag size={20} />} 
          label="Marketplace" 
          collapsed={collapsed} 
          active={activePath === '/marketplace'} 
        />
        <NavItem 
          to="/security"
          icon={<ShieldAlert size={20} />} 
          label="Security Center" 
          collapsed={collapsed} 
          active={activePath === '/security'} 
        />
        <NavItem 
          to="/mcp"
          icon={<Layers size={20} />} 
          label="MCP Center" 
          collapsed={collapsed} 
          active={activePath === '/mcp'} 
        />
        <NavItem 
          to="/trust"
          icon={<ShieldCheck size={20} />} 
          label="Device Trust" 
          collapsed={collapsed} 
          active={activePath === '/trust'} 
        />
        <NavItem 
          to="/pattern-compiler"
          icon={<Terminal size={20} />} 
          label="Pattern Compiler" 
          collapsed={collapsed} 
          active={activePath === '/pattern-compiler'} 
        />
        <NavItem 
          to="/intelligence-lattice"
          icon={<Layers size={20} />} 
          label="Intelligence Lattice" 
          collapsed={collapsed} 
          active={activePath === '/intelligence-lattice'} 
        />
        <NavItem 
          to="/governance"
          icon={<ShieldCheck size={20} />} 
          label="Governance" 
          collapsed={collapsed} 
          active={activePath === '/governance'} 
        />
      </nav>

      <div style={{ padding: '20px', borderTop: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
        <NavItem 
          to="/settings"
          icon={<Settings size={20} />} 
          label="Settings" 
          collapsed={collapsed} 
          active={activePath === '/settings'} 
        />
      </div>
    </aside>
  );
};

const NavItem: React.FC<{ 
  to: string,
  icon: React.ReactNode, 
  label: string, 
  collapsed: boolean, 
  active?: boolean
}> = ({ to, icon, label, collapsed, active }) => (
  <Link 
    to={to}
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '12px',
      borderRadius: '8px',
      backgroundColor: active ? 'rgba(0, 242, 255, 0.1)' : 'transparent',
      color: active ? 'var(--color-gas)' : 'var(--color-text-secondary)',
      cursor: 'pointer',
      marginBottom: '4px',
      transition: 'all 0.2s ease',
      justifyContent: collapsed ? 'center' : 'flex-start',
      textDecoration: 'none'
    }}
  >
    {icon}
    {!collapsed && <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{label}</span>}
  </Link>
);

export default LeftPanel;
