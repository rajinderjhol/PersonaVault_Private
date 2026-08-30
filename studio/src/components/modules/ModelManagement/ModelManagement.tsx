import React, { useEffect } from 'react';
import { useModelStore } from '../../../store/modelStore';
import { RefreshCw, Check, Server } from 'lucide-react';

const ModelManagement: React.FC = () => {
  const { models, selectedModel, isLoading, fetchModels, setSelectedModel } = useModelStore();

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return (
    <div style={{ padding: '24px', color: 'var(--color-text-primary)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h2 style={{ margin: 0 }}>Model Management</h2>
        <button 
          onClick={fetchModels} 
          disabled={isLoading}
          style={{ 
            background: 'var(--color-bg-tertiary)', 
            border: 'none', 
            padding: '8px 16px', 
            borderRadius: '6px', 
            color: 'white', 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px' }}>
        {models.map((model) => (
          <div 
            key={model.model_name}
            onClick={() => setSelectedModel(model.model_name)}
            style={{
              backgroundColor: 'var(--color-bg-secondary)',
              padding: '20px',
              borderRadius: '12px',
              border: `1px solid ${selectedModel === model.model_name ? 'var(--color-gas)' : 'var(--glass-border)'}`,
              cursor: 'pointer',
              position: 'relative'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
              <Server size={24} color="var(--color-text-secondary)" />
              <h3 style={{ margin: 0 }}>{model.model_name}</h3>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{model.description}</p>
            
            {selectedModel === model.model_name && (
              <div style={{ position: 'absolute', top: '12px', right: '12px', color: 'var(--color-gas)' }}>
                <Check size={20} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ModelManagement;
