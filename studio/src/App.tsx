import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Dashboard } from './pages/Dashboard';
import { Search } from './pages/Search';
import { AgentSwarmUI } from './components/chat/AgentSwarmUI';
import { TemporalIntelligenceWidget } from './components/dashboard/TemporalIntelligenceWidget';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <header className="app-header">
          <h1>PersonaVault Studio</h1>
          <nav>
            <a href="/">Dashboard</a>
            <a href="/search">Search</a>
            <a href="/chat">Chat</a>
          </nav>
        </header>
        
        <main className="app-main">
          <Routes>
            <Route path="/" element={
              <div className="page-content">
                <Dashboard />
                <TemporalIntelligenceWidget timeRange="30d" />
                <AgentSwarmUI isActive={false} messages={[]} />
              </div>
            } />
            <Route path="/search" element={<Search />} />
            <Route path="/chat" element={
              <div className="page-content">
                <AgentSwarmUI isActive={true} messages={[]} />
              </div>
            } />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
