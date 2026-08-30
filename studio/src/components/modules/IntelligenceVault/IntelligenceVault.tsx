import React from 'react';
import ThermodynamicView from './components/ThermodynamicView';
import CrystallizationDashboard from './components/CrystallizationDashboard';
import PhaseControls from './components/PhaseControls';
import SnowflakeManager from './components/SnowflakeManager';

const IntelligenceVault: React.FC = () => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      gap: '24px',
      height: '100%',
      overflowY: 'auto',
      paddingRight: '12px'
    }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <ThermodynamicView />
          <CrystallizationDashboard />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <PhaseControls />
          <SnowflakeManager />
        </div>
      </div>
    </div>
  );
};

export default IntelligenceVault;
