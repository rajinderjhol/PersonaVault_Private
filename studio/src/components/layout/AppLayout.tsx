import React from 'react';
import LeftPanel from './LeftPanel';
import CorePanel from './CorePanel';
import RightPanel from './RightPanel';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div style={{
      display: 'flex',
      width: '100vw',
      height: '100vh',
      overflow: 'hidden',
      colorScheme: 'dark'
    }}>
      {/* Sidebar Navigation */}
      <LeftPanel />

      {/* Main Content Area */}
      <CorePanel>
        {children}
      </CorePanel>

      {/* Contextual Intelligence Panel */}
      <RightPanel />
    </div>
  );
};

export default AppLayout;
