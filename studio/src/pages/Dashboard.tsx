import React, { useState } from 'react';
import { TimeFilter } from '../components/dashboard/TimeFilter';
import { TemporalIntelligenceWidget } from '../components/dashboard/TemporalIntelligenceWidget';
import { useDashboardMetricsQuery } from '../hooks/query/useDashboardMetricsQuery';
import styles from './Dashboard.module.css';

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

  const { data: metrics, isLoading } = useDashboardMetricsQuery(filter);

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
            <div className={styles.metricLabel}>Total Decisions</div>
            <div className={styles.metricValue}>{metrics?.total_events || 0}</div>
            <div className={`${styles.metricTrend} ${metrics?.temporal_trend === 'improving' ? styles.trendUp : ''}`}>
              {metrics?.temporal_trend || 'stable'}
            </div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>🎯</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Avg Confidence</div>
            <div className={styles.metricValue}>{((metrics?.confidence_avg || 0) * 100).toFixed(1)}%</div>
            <div className={styles.metricTrend}>+2.3%</div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>⚡</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Decision Velocity</div>
            <div className={styles.metricValue}>{metrics?.velocity?.toFixed(2) || '0.00'}</div>
            <div className={styles.metricTrend}>
              {metrics?.velocity && metrics.velocity > 0.5 ? '🚀 accelerating' : '⚖️ stable'}
            </div>
          </div>
        </div>

        <div className={styles.metricCard}>
          <div className={styles.metricIcon}>⚠️</div>
          <div className={styles.metricContent}>
            <div className={styles.metricLabel}>Aging Patterns</div>
            <div className={styles.metricValue}>{metrics?.aging_patterns_count || 0}</div>
            <div className={styles.metricTrend}>
              {metrics?.aging_patterns_count && metrics.aging_patterns_count > 0 ? 'needs review' : '✅ healthy'}
            </div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '2rem' }}>
        <TemporalIntelligenceWidget timeRange={filter.range} />
      </div>
    </div>
  );
};
