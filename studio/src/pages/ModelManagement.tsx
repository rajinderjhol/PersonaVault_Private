import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { useV2Models, useV2ModelMetrics, useV2Providers } from '../hooks/query/v2/useV2Models';
import { ModelCard } from '../components/models/ModelCard';
import { ModelBOM } from '../components/models/ModelBOM';
import { ProviderTable } from '../components/models/ProviderTable';
import { ProviderStats } from '../components/models/ProviderStats';
import { useV2PullModel } from '../hooks/query/v2/useV2PullModel';
import { useV2DeleteModel } from '../hooks/query/v2/useV2DeleteModel';
import styles from './ModelManagement.module.css';

export const ModelManagement: React.FC = () => {
  const { data: models, isLoading: modelsLoading, error: modelsError } = useV2Models();
  const { data: metrics, isLoading: metricsLoading } = useV2ModelMetrics();
  const { data: providers, isLoading: providersLoading } = useV2Providers();
  const [newModelName, setNewModelName] = useState('');
  const [activeProvider, setActiveProvider] = useState<string>('ollama');
  
  const { mutate: pullModel, isPending: isPulling } = useV2PullModel();
  const { mutate: deleteModel } = useV2DeleteModel();

  useEffect(() => {
    const fetchActiveProvider = async () => {
        try {
            const res = await apiClient.get('/admin/dashboard/config/primary-ai-provider');
            setActiveProvider(res.primary_provider || 'ollama');
        } catch (e) {
            console.error('Failed to fetch active provider', e);
        }
    };
    fetchActiveProvider();
  }, []);

  const handleProviderChange = async (provider: string) => {
    try {
        await apiClient.post('/admin/dashboard/config/primary-ai-provider', { provider });
        setActiveProvider(provider);
        alert(`Provider set to ${provider}`);
    } catch (e) {
        alert('Failed to update provider');
    }
  };

  if (modelsError) {
    return <div className={styles.container}><h3>Failed to load models</h3></div>;
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h1 className={styles.title}>📦 Model Management</h1>
      </header>

      {/* 1. Primary AI Provider */}
      <section className={styles.card}>
        <h3 className={styles.cardTitle}>🎯 Primary AI Provider</h3>
        <p className={styles.description}>Select the default AI provider for all system queries.</p>
        <div className={styles.configRow}>
           <select className={styles.inputField} value={activeProvider} onChange={(e) => handleProviderChange(e.target.value)}>
             {providers?.map((p: any) => (
               <option key={p.id} value={p.id}>{p.name}</option>
             ))}
           </select>
           <span className={styles.tag}>✅ Active: {activeProvider}</span>
        </div>
      </section>

      {/* 2. Provider Status */}
      <section className={styles.card}>
        <ProviderStats stats={metrics?.providerStats || {}} />
      </section>

      {/* 3. AI Providers Table */}
      <section className={styles.card}>
        <ProviderTable providers={providers || []} onEdit={() => {}} onDelete={() => {}} />
      </section>

      {/* 4. Reload API Keys */}
      <section className={styles.card}>
        <h3 className={styles.cardTitle}>🔄 Reload API Keys</h3>
        <p className={styles.description}>Load API keys from .env file into the database.</p>
        <button className={styles.actionBtn}>Reload from .env</button>
      </section>

      {/* 5. AI Bill of Materials */}
      <section className={styles.card}>
        <ModelBOM models={models || []} activeModel={models?.find(m => m.isActive)?.name || 'None'} />
      </section>

      {/* 6. Pull New Model */}
      <section className={styles.card}>
        <h3 className={styles.cardTitle}>📥 Pull New Ollama Model</h3>
        <div className={styles.pullRow}>
            <input 
              type="text" 
              placeholder="e.g. llama3.2:3b" 
              className={styles.inputField} 
              value={newModelName}
              onChange={(e) => setNewModelName(e.target.value)}
            />
            <button 
              className={styles.actionBtn} 
              disabled={isPulling}
              onClick={() => pullModel(newModelName)}
            >
              {isPulling ? 'Pulling...' : 'Pull Model'}
            </button>
        </div>
      </section>

      {/* 7. Installed Ollama Models */}
      <section className={styles.card}>
        <h3 className={styles.cardTitle}>📦 Installed Ollama Models</h3>
        <div className={styles.cardsContainer}>
          {modelsLoading ? <p>Loading models...</p> : (
            models?.map(model => (
              <ModelCard 
                key={model.id}
                model={model}
                isActive={model.isActive}
                onSetActive={() => {}}
                onDelete={(name) => deleteModel(name)}
              />
            ))
          )}
        </div>
      </section>
    </div>
  );
};
