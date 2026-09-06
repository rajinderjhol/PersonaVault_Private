import { useLocation } from 'react-router-dom';
import { CommandBar } from './CommandBar';
import LeftPanel from './LeftPanel';
import CorePanel from './CorePanel';
import RightPanel from './RightPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const isCognitiveLab = location.pathname === '/chat';

  return (
    <div className="app-layout" style={{
      display: 'flex',
      flexDirection: 'column',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      backgroundColor: 'var(--color-bg-primary)'
    }}>
      {/* Sovereign Cockpit Command Bar */}
      <CommandBar />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar Navigation */}
        <LeftPanel />

        {/* Main Content Area */}
        <CorePanel>
          {children}
        </CorePanel>

        {/* Contextual Intelligence Panel - Hidden in Cognitive Lab as it has its own cockpit */}
        {!isCognitiveLab && <RightPanel />}
      </div>
    </div>
  );
};

export default AppLayout;
