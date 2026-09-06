import React from 'react';
import { useV2DashboardMetrics } from '../hooks/query/v2/useV2DashboardMetrics';
import { useEnvironmentStore } from '../store/environmentStore';
import { KPICard } from '../components/dashboard/KPICard';
import { DashboardSkeleton } from '../components/dashboard/DashboardSkeleton';
import styles from './Dashboard.module.css';

export const Dashboard: React.FC = () => {
  const { currentEnvId } = useEnvironmentStore();
  const { data: metrics, isLoading, error } = useV2DashboardMetrics();
  
  if (isLoading) return <DashboardSkeleton />;
  if (error) return <div className={styles.dashboard}>Error: {(error as Error).message}</div>;

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h1>🧠 Intelligence Pulse</h1>
      </div>

      <div className={styles.metricsGrid} style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
        <KPICard title="Compression" value="1.2M:1" trend="12%" trendDirection="up" />
        <KPICard title="Confidence" value={`${(metrics?.confidence ?? 0)}%`} trend="2.1%" trendDirection="up" />
        <KPICard title="Memories" value={(metrics?.total_memories ?? 0).toLocaleString()} trend="47 new" trendDirection="up" />
        <KPICard title="Avg Response" value={`${metrics?.latency ?? 0}ms`} trend="0.8s" trendDirection="down" />
      </div>

      <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '1.5rem', borderRadius: '12px', border: '1px solid var(--glass-border)' }}>
        <h3>📈 Intelligence Growth (Last 30 Days)</h3>
        {/* Placeholder for growth chart */}
        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>
          [Growth Chart Visualization]
        </div>
      </div>
    </div>
  );
};
