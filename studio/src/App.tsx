import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import AppLayout from './components/layout/AppLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import Login from './components/modules/Login/Login';

import { WSMonitor } from './pages/WSMonitor';
import { ModelManagement } from './pages/ModelManagement';
import { RoleManagement } from './pages/Admin/RoleManagement';
import { UserManagement } from './pages/Admin/UserManagement';
import { VeriLinkStatus } from './pages/VeriLinkStatus';
import { APIExplorer } from './pages/APIExplorer';
import { MemoryLattice } from './pages/MemoryLattice';
import { IntelligenceVault } from './pages/IntelligenceVault';
import { SnowflakeManager } from './pages/SnowflakeManager';
import { SystemHealth } from './pages/SystemHealth';
import { CrystallizationDashboard } from './pages/CrystallizationDashboard';
import { Governance } from './pages/Governance';
import { ConstitutionEditor } from './pages/ConstitutionEditor';
import { PolicyManagement } from './pages/PolicyManagement';
import { Profile } from './pages/Profile';
import { DeviceTrust } from './pages/DeviceTrust';
import { MCPCenter } from './pages/MCPCenter';
import { UniversalSearch } from './pages/UniversalSearch';
import { AdminTools } from './pages/AdminTools';
import { IntelligenceLattice } from './pages/IntelligenceLattice';
import { Governance } from './pages/Governance';
import { PatternCompiler } from './pages/PatternCompiler';
import { SecurityCenter } from './pages/SecurityCenter';
import { Dashboard } from './pages/Dashboard';
import { Search } from './pages/Search';
import { DataIngestion } from './pages/DataIngestion';
import { PolicySimulator } from './pages/PolicySimulator';
import { Marketplace } from './pages/Marketplace';

// Modules
import CognitiveLab from './components/modules/CognitiveLab/CognitiveLab';

function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/*" element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/chat" element={<CognitiveLab />} />
                <Route path="/search" element={<Search />} />
                <Route path="/models" element={<ModelManagement />} />
                <Route path="/intelligence-vault" element={<IntelligenceVault />} />
                <Route path="/ingestion" element={<DataIngestion />} />
                <Route path="/simulator" element={<PolicySimulator />} />
                
                <Route path="/profile" element={<Profile />} />
                <Route path="/marketplace" element={<Marketplace />} />
                <Route path="/security" element={<SecurityCenter />} />
                <Route path="/mcp" element={<MCPCenter />} />
                <Route path="/trust" element={<DeviceTrust />} />
                <Route path="/universal-search" element={<UniversalSearch />} />
                <Route path="/admin-tools" element={<AdminTools />} />
                <Route path="/intelligence-lattice" element={<IntelligenceLattice />} />
                <Route path="/governance" element={<Governance />} />
                <Route path="/compiler" element={<PatternCompiler />} />
                <Route path="/governance/policies" element={<PolicyManagement />} />
                <Route path="/governance/constitution" element={<ConstitutionEditor />} />
                <Route path="/cognitive/crystallization" element={<CrystallizationDashboard />} />
                <Route path="/cognitive/snowflakes" element={<SnowflakeManager />} />
                <Route path="/cognitive/memory-lattice" element={<MemoryLattice />} />
                <Route path="/admin/health" element={<SystemHealth />} />
                <Route path="/admin/users" element={<UserManagement />} />
                <Route path="/admin/roles" element={<RoleManagement />} />
                <Route path="/dev/ws-monitor" element={<WSMonitor />} />
                <Route path="/dev/api-explorer" element={<APIExplorer />} />
                <Route path="/governance/verilink" element={<VeriLinkStatus />} />
                <Route path="/settings" element={<div>Settings Component</div>} />
                
                {/* Fallback */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        } />
      </Routes>
    </Router>
  );
}

export default App;
