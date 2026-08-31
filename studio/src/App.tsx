import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import AppLayout from './components/layout/AppLayout';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import Login from './components/modules/Login/Login';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Search } from './pages/Search';
import { DataIngestion } from './pages/DataIngestion';
import { Simulator } from './pages/Simulator';
import { Marketplace } from './pages/Marketplace';

// Components
import { AgentSwarmUI } from './components/chat/AgentSwarmUI';

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
                <Route path="/chat" element={<AgentSwarmUI isActive={true} />} />
                <Route path="/search" element={<Search />} />
                <Route path="/ingestion" element={<DataIngestion />} />
                <Route path="/simulator" element={<Simulator />} />
                
                {/* Placeholder routes */}
                <Route path="/marketplace" element={<Marketplace />} />
                <Route path="/security" element={<div>Security Center Component</div>} />
                <Route path="/mcp" element={<div>MCP Center Component</div>} />
                <Route path="/trust" element={<div>Device Trust Component</div>} />
                <Route path="/compiler" element={<div>Pattern Compiler Component</div>} />
                <Route path="/governance" element={<div>Governance Component</div>} />
                <Route path="/models" element={<div>Model Management Component</div>} />
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
