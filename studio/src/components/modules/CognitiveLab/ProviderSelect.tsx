import { useEffect, useState } from 'react';
import { apiClient } from '../../../api/client';

export const ProviderSelect = ({ value, onChange }: { value: string, onChange: (val: string) => void }) => {
  const [providers, setProviders] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await apiClient.get('/admin/config/primary-ai-provider');
        // Based on the backend implementation, it returns {"primary_provider": "..."}
        setProviders([response.data.primary_provider || 'ollama']);
      } catch (error) {
        console.error('Failed to fetch providers:', error);
        setProviders(['ollama', 'groq', 'gemini']); // Fallback
      } finally {
        setLoading(false);
      }
    };
    fetchProviders();
  }, []);

  if (loading) return <select disabled><option>Loading...</option></select>;

  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} style={{ padding: '8px', borderRadius: '4px', background: 'var(--color-bg-secondary)', color: 'white' }}>
      {providers.map((provider) => (
        <option key={provider} value={provider}>
          {provider}
        </option>
      ))}
    </select>
  );
};
