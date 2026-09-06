import { useEffect, useState } from 'react';
import { apiClient } from '../../../api/client';

export const ProviderSelect = ({ value, onChange }: { value: string, onChange: (val: string) => void }) => {
  const [providers, setProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        // Fetch all providers
        const response = await apiClient.get('/admin/config/ai-providers/cloud');
        const providersList = ['ollama', ...response.map((p: any) => p.name)];
        setProviders(providersList);
      } catch (error) {
        console.error('Failed to fetch providers:', error);
        setProviders(['ollama', 'groq', 'gemini', 'deepseek']); // Fallback
      } finally {
        setLoading(false);
      }
    };
    fetchProviders();
  }, []);

  const handleProviderChange = async (newProvider: string) => {
    try {
      await apiClient.post('/admin/config/primary-ai-provider', { provider: newProvider });
      onChange(newProvider);
      // Assuming a toast utility exists, if not, simple console log for now
      console.log(`Primary provider set to ${newProvider}`);
    } catch (error) {
      console.error('Failed to set provider:', error);
    }
  };

  if (loading) return <select disabled><option>Loading...</option></select>;

  return (
    <select value={value} onChange={(e) => handleProviderChange(e.target.value)} style={{ padding: '8px', borderRadius: '4px', background: 'var(--bg-secondary)', color: 'var(--color-text-primary)' }}>
      {providers.map((provider) => (
        <option key={provider} value={provider}>
          {provider}
        </option>
      ))}
    </select>
  );
};
