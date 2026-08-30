import { CalendarManager } from './components/modules/Integrations/CalendarManager';
import { DeviceManager } from './components/modules/Integrations/DeviceManager';
import React from 'react';
import AppLayout from './components/layout/AppLayout';
import CognitiveLab from './components/modules/CognitiveLab/CognitiveLab';
import IntelligenceVault from './components/modules/IntelligenceVault/IntelligenceVault';
import MCPCenter from './components/modules/MCPCenter/MCPCenter';
import DeviceTrust from './components/modules/DeviceTrust/DeviceTrust';
import SovereignControl from './components/modules/SovereignControl/SovereignControl';
import PatternCompiler from './components/modules/PatternCompiler/PatternCompiler';
import DeveloperConsole from './components/modules/DeveloperConsole/DeveloperConsole';
import Governance from './components/modules/Governance/Governance';
import Marketplace from './components/modules/Marketplace/Marketplace';
import SecurityCenter from './components/modules/SecurityCenter/SecurityCenter';
import ModelManagement from './components/modules/ModelManagement/ModelManagement';
import Login from './components/modules/Login/Login';
import { useNavigationStore } from './components/layout/LeftPanel';
import { useAuthStore } from './store/authStore';
import { useSovereignStore } from './store/sovereignStore';
import { useOffline } from './hooks/useOffline';
import { motion, AnimatePresence } from 'framer-motion';
import { WifiOff, ShieldAlert } from 'lucide-react';
import './styles/variables.css';
import { useEffect } from 'react';

function App() {
  const { activeModule } = useNavigationStore();
  const { airGapped, executionMode } = useSovereignStore();
  const { isOffline } = useOffline();
  const { isAuthenticated, isAuthenticating, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isAuthenticating) {
    return <div style={{ color: 'white', display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;
  }

  if (!isAuthenticated) {
    return <Login />;
  }

  return (
    <AppLayout>
      <AnimatePresence mode="wait">
        <motion.div
          key={activeModule}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.2 }}
          style={{ height: '100%' }}
        >
          {activeModule === 'dashboard' && <Dashboard />}
          {activeModule === 'lab' && <CognitiveLab />}
          {activeModule === 'vault' && <IntelligenceVault />}
          {activeModule === 'mcp' && <MCPCenter />}
          {activeModule === 'trust' && <DeviceTrust />}
          {activeModule === 'sovereign' && <SovereignControl />}
          {activeModule === 'compiler' && <PatternCompiler />}
          {activeModule === 'console' && <DeveloperConsole />}
          {activeModule === 'governance' && <Governance />}
          {activeModule === 'marketplace' && <Marketplace />}
          {activeModule === 'security' && <SecurityCenter />}
          {activeModule === 'models' && <ModelManagement />}
          {activeModule === 'calendar' && <CalendarManager />}
          {activeModule === 'devices' && <DeviceManager />}
        </motion.div>
      </AnimatePresence>

      {/* Global Status Overlays */}
      <div style={{ position: 'fixed', top: '10px', right: '340px', display: 'flex', gap: '8px', zIndex: 100 }}>
        {isOffline && (
          <div style={{
            backgroundColor: 'rgba(245, 158, 11, 0.9)',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '0.7rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center', gap: '6px',
            boxShadow: '0 0 10px rgba(245, 158, 11, 0.3)'
          }}>
            <WifiOff size={12} /> OFFLINE MODE
          </div>
        )}
        
        {airGapped && (
          <div style={{
            backgroundColor: 'rgba(239, 68, 68, 0.9)',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '20px',
            fontSize: '0.7rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center', gap: '6px',
            boxShadow: '0 0 10px rgba(239, 68, 68, 0.3)'
          }}>
            <ShieldAlert size={12} /> AIR-GAPPED
          </div>
        )}
      </div>

      {executionMode === 'simulation' && (
        <div style={{
          position: 'fixed',
          bottom: '42px',
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: 'var(--color-liquid)',
          color: 'white',
          padding: '4px 20px',
          borderRadius: '4px 4px 0 0',
          fontSize: '0.75rem',
          fontWeight: 600,
          zIndex: 100,
          letterSpacing: '0.05em'
        }}>
          SIMULATION ACTIVE - NO SIDE EFFECTS
        </div>
      )}
    </AppLayout>
  );
}

const Dashboard: React.FC = () => (
  <div style={{ 
    display: 'flex', 
    flexDirection: 'column', 
    gap: '24px', 
    maxWidth: '1200px', 
    margin: '0 auto' 
  }}>
    {/* Welcome Section */}
    <div style={{ 
      padding: '40px', 
      borderRadius: '16px', 
      background: 'linear-gradient(135deg, var(--color-bg-secondary) 0%, var(--color-bg-primary) 100%)',
      border: '1px solid var(--glass-border)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      <div style={{ position: 'relative', zIndex: 2 }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '8px', fontWeight: 700 }}>Sovereign Decision Studio</h1>
        <p style={{ color: 'var(--color-text-secondary)', fontSize: '1.1rem', maxWidth: '600px' }}>
          Welcome back to PersonaVault. Your cognitive swarm is active and monitoring 6 behavior packs.
        </p>
      </div>
      <div style={{ 
        position: 'absolute', 
        top: '-50px', 
        right: '-50px', 
        width: '300px', 
        height: '300px', 
        borderRadius: '50%', 
        background: 'radial-gradient(circle, var(--color-gas) 0%, transparent 70%)',
        opacity: 0.1,
        filter: 'blur(40px)'
      }} />
    </div>

    {/* Stats Grid */}
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
      <StatCard title="Memory Hit Rate" value="94.2%" trend="+2.4%" color="var(--color-gas)" />
      <StatCard title="Decision Confidence" value="0.98" trend="Stable" color="var(--color-liquid)" />
      <StatCard title="Active Signals" value="1,284" trend="+142" color="var(--color-accent)" />
      <StatCard title="Token Efficiency" value="10,000:1" trend="Maximized" color="var(--color-ice)" />
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
      <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '20px' }}>Recent Intelligence Events</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <EventItem time="2m ago" msg="Security Pack detected data drift in Edge Node #01" />
          <EventItem time="15m ago" msg="Interaction #824 crystallized into Pattern #42" />
          <EventItem time="1h ago" msg="Automated policy update: PHI Tokenization v2.1" />
        </div>
      </div>
      <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '20px' }}>System Sovereignty</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Local Context Ownership</span>
            <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>100% Verified</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Provider Transparency</span>
            <span style={{ color: 'var(--color-gas)', fontWeight: 600 }}>Groq / Open Source</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Governance Status</span>
            <span style={{ color: 'var(--color-ice)', fontWeight: 600 }}>Active - VeriLink Stable</span>
          </div>
        </div>
      </div>
    </div>
  </div>
);

const StatCard: React.FC<{ title: string, value: string, trend: string, color: string }> = ({ title, value, trend, color }) => (
  <div style={{ 
    padding: '24px', 
    backgroundColor: 'var(--color-bg-secondary)', 
    borderRadius: '12px', 
    border: '1px solid var(--glass-border)',
    display: 'flex',
    flexDirection: 'column',
    gap: '8px'
  }}>
    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{title}</span>
    <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
      <span style={{ fontSize: '1.8rem', fontWeight: 700, color: color }}>{value}</span>
      <span style={{ fontSize: '0.85rem', color: 'var(--color-success)' }}>{trend}</span>
    </div>
  </div>
);

const EventItem: React.FC<{ time: string, msg: string }> = ({ time, msg }) => (
  <div style={{ display: 'flex', gap: '12px', fontSize: '0.85rem' }}>
    <span style={{ color: 'var(--color-text-muted)', minWidth: '60px' }}>{time}</span>
    <span style={{ color: 'var(--color-text-primary)' }}>{msg}</span>
  </div>
);

export default App;
