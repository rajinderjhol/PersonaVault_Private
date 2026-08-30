import { useEffect, useState } from 'react';
import { apiClient } from '../../../api/client';

export const Metrics = () => {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await apiClient.get('/admin/dashboard/metrics');
        setMetrics(response.data);
      } catch (error) {
        console.error('Failed to fetch metrics:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchMetrics();
  }, []);

  if (loading) return <div style={{ color: 'white' }}>Loading metrics...</div>;
  if (!metrics) return <div style={{ color: 'white' }}>No metrics available</div>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', padding: '16px' }}>
      <MetricCard label="Memory Hit Rate" value={metrics.memory_hit_rate || 0} />
      <MetricCard label="Confidence" value={metrics.confidence || 0} />
      <MetricCard label="Token Efficiency" value={metrics.token_efficiency || 0} />
    </div>
  );
};

const MetricCard = ({ label, value }: { label: string, value: number }) => (
  <div style={{ background: 'var(--color-bg-secondary)', padding: '20px', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
    <div style={{ color: 'var(--color-text-secondary)', fontSize: '0.8rem', marginBottom: '8px' }}>{label}</div>
    <div style={{ color: 'white', fontSize: '1.5rem', fontWeight: 600 }}>{value}</div>
  </div>
);
