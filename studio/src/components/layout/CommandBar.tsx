import React, { useEffect } from 'react';
import { useStudioStore } from '../../store/studioStore';
import { usePackStore } from '../../store/packStore';
import { useSovereignStore } from '../../store/sovereignStore';
import { useEnvironmentStore } from '../../store/environmentStore';
import { X, Plus } from 'lucide-react';
import './CommandBar.css';

export const CommandBar: React.FC = () => {
  const { activePackIds, removePack } = useStudioStore();
  const { installedPacks } = usePackStore();
  const { executionMode } = useSovereignStore();
  const { environments, currentEnvId, setCurrentEnvironment, fetchEnvironments, createEnvironment } = useEnvironmentStore();

  useEffect(() => {
    fetchEnvironments();
  }, []);

  const handleCreateEnv = async () => {
    const name = window.prompt('Enter environment name:');
    if (name) {
      await createEnvironment(name);
    }
  };

  const activePacks = installedPacks.filter((p) => activePackIds.includes(p.id));

  return (
    <div className="command-bar">
      <div className="active-packs">
        <div className="env-controls" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <select 
            className="env-select" 
            value={currentEnvId || ''} 
            onChange={(e) => {
              console.log("DEBUG: Changing environment to:", e.target.value);
              setCurrentEnvironment(e.target.value);
            }}
          >
            <option value="">Select Environment</option>
            {environments.map(env => <option key={env.id} value={env.id}>{env.name}</option>)}
          </select>
          <button 
            className="new-env-btn" 
            onClick={handleCreateEnv}
            title="Create New Environment"
            style={{ 
              background: 'rgba(0, 242, 255, 0.1)', 
              border: '1px solid var(--color-gas)', 
              color: 'var(--color-gas)',
              borderRadius: '4px',
              padding: '4px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center'
            }}
          >
            <Plus size={16} />
          </button>
        </div>
        {activePacks.map((pack) => (
          <div key={pack.id} className="pack-chip">
            {pack.name}
            <button onClick={() => removePack(pack.id)}><X size={14} /></button>
          </div>
        ))}
      </div>

      <div className="observability">
        <div className={`mode-badge mode-${executionMode}`}>
          {executionMode.toUpperCase()}
        </div>
      </div>
    </div>
  );
};
