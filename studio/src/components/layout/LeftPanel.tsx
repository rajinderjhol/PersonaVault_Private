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
  Smartphone
} from 'lucide-react';
import { create } from 'zustand';

// UI State Store for Navigation
interface NavigationState {
  activeModule: string;
  collapsed: boolean;
  setActiveModule: (module: string) => void;
  toggleCollapsed: () => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  activeModule: 'lab',
  collapsed: false,
  setActiveModule: (module) => set({ activeModule: module }),
  toggleCollapsed: () => set((state) => ({ collapsed: !state.collapsed })),
}));

const LeftPanel: React.FC = () => {
  const { activeModule, collapsed, setActiveModule, toggleCollapsed } = useNavigationStore();

  return (
    <aside style={{
      width: collapsed ? 'var(--left-panel-collapsed-width)' : 'var(--left-panel-width)',
      height: '100vh',
      backgroundColor: 'var(--color-bg-secondary)',
      borderRight: '1px solid var(--glass-border)',
      transition: 'width var(--transition-speed) ease',
      display: 'flex',
      flexDirection: 'column',
      position: 'relative',
      zIndex: 10
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
          icon={<LayoutDashboard size={20} />} 
          label="Dashboard" 
          collapsed={collapsed} 
          active={activeModule === 'dashboard'} 
          onClick={() => setActiveModule('dashboard')}
        />
        <NavItem 
          icon={<MessageSquare size={20} />} 
          label="Cognitive Lab" 
          collapsed={collapsed} 
          active={activeModule === 'lab'} 
          onClick={() => setActiveModule('lab')}
        />
        <NavItem 
          icon={<ShoppingBag size={20} />} 
          label="Marketplace" 
          collapsed={collapsed} 
          active={activeModule === 'marketplace'} 
          onClick={() => setActiveModule('marketplace')}
        />
        <NavItem 
          icon={<ShieldAlert size={20} />} 
          label="Security Center" 
          collapsed={collapsed} 
          active={activeModule === 'security'} 
          onClick={() => setActiveModule('security')}
        />
        <NavItem 
          icon={<Database size={20} />} 
          label="Intelligence Vault" 
          collapsed={collapsed} 
          active={activeModule === 'vault'} 
          onClick={() => setActiveModule('vault')}
        />
        <NavItem 
          icon={<Layers size={20} />} 
          label="MCP Center" 
          collapsed={collapsed} 
          active={activeModule === 'mcp'} 
          onClick={() => setActiveModule('mcp')}
        />
        <NavItem 
          icon={<ShieldCheck size={20} />} 
          label="Device Trust" 
          collapsed={collapsed} 
          active={activeModule === 'trust'} 
          onClick={() => setActiveModule('trust')}
        />
        <NavItem 
          icon={<Terminal size={20} />} 
          label="Pattern Compiler" 
          collapsed={collapsed} 
          active={activeModule === 'compiler'} 
          onClick={() => setActiveModule('compiler')}
        />
        <NavItem 
          icon={<ShieldCheck size={20} />} 
          label="Governance" 
          collapsed={collapsed} 
          active={activeModule === 'governance'} 
          onClick={() => setActiveModule('governance')}
        />
        <NavItem 
          icon={<Calendar size={20} />} 
          label="Calendar" 
          collapsed={collapsed} 
          active={activeModule === 'calendar'} 
          onClick={() => setActiveModule('calendar')}
        />
        <NavItem 
          icon={<Smartphone size={20} />} 
          label="Devices" 
          collapsed={collapsed} 
          active={activeModule === 'devices'} 
          onClick={() => setActiveModule('devices')}
        />
        <NavItem 
          icon={<Cpu size={20} />} 
          label="Sovereign Control" 
          collapsed={collapsed} 
          active={activeModule === 'sovereign'} 
          onClick={() => setActiveModule('sovereign')}
        />
        <NavItem 
          icon={<Server size={20} />} 
          label="Model Management" 
          collapsed={collapsed} 
          active={activeModule === 'models'} 
          onClick={() => setActiveModule('models')}
        />
        <NavItem 
          icon={<Terminal size={20} />} 
          label="Dev Console" 
          collapsed={collapsed} 
          active={activeModule === 'console'} 
          onClick={() => setActiveModule('console')}
        />
      </nav>

      <div style={{ padding: '20px', borderTop: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', justifyContent: collapsed ? 'center' : 'flex-start' }}>
          <Settings size={20} />
          {!collapsed && <span>Settings</span>}
        </div>
      </div>
    </aside>
  );
};

const NavItem: React.FC<{ 
  icon: React.ReactNode, 
  label: string, 
  collapsed: boolean, 
  active?: boolean,
  onClick: () => void 
}> = ({ icon, label, collapsed, active, onClick }) => (
  <div 
    onClick={onClick}
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
      justifyContent: collapsed ? 'center' : 'flex-start'
    }}
  >
    {icon}
    {!collapsed && <span style={{ fontSize: '0.9rem', fontWeight: 500 }}>{label}</span>}
  </div>
);

export default LeftPanel;
