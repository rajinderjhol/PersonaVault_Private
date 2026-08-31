import React, { useState } from 'react';
import { TimeFilter } from '../components/dashboard/TimeFilter';
import { TemporalIntelligenceWidget } from '../components/dashboard/TemporalIntelligenceWidget';
import { useDashboardMetricsQuery } from '../hooks/query/useDashboardMetricsQuery';
import styles from './Dashboard.module.css';

interface DashboardMetrics {
  memories?: {
    total: number;
  };
  sessions?: {
    active: number;
  };
  system?: {
    thermodynamics?: {
      crystallization_rate: number;
    };
    storage_used?: {
      used_percent: number;
    };
  };
}

export const Dashboard: React.FC = () => {
  const [filter, setFilter] = useState<{
    startDate: string;
    endDate: string;
    range: string;
  }>({
    startDate: '',
    endDate: '',
    range: '30d'
  });

  const { data, isLoading } = useDashboardMetricsQuery(filter);
  const metrics = data as DashboardMetrics | undefined;

  const handleFilterChange = (startDate: string, endDate: string, range: string) => {
    setFilter({ startDate, endDate, range });
  };

  return (
    <div className={styles.dashboard}>
      <div className={styles.header}>
        <h1>Decision Intelligence Dashboard</h1>
        <TimeFilter onFilterChange={handleFilterChange} initialRange="30d" />
      </div>

      <div className={styles.metricsGrid}>
        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>📊</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Total Memories</div>
            <div className={styles.metricValue}>{metrics?.memories?.total ?? 0}</div>
            <div className={styles.metricTrend}>stable</div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>🎯</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Active Sessions</div>
            <div className={styles.metricValue}>{metrics?.sessions?.active ?? 0}</div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>⚡</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Crystallization Rate</div>
            <div className={styles.metricValue}>{metrics?.system?.thermodynamics?.crystallization_rate?.toFixed(2) ?? '0.00'}</div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>⚠️</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Storage Used</div>
            <div className={styles.metricValue}>{metrics?.system?.storage_used?.used_percent ?? 0}%</div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <TemporalIntelligenceWidget timeRange={filter.range} />
      </div>
    </div>
  );
};
