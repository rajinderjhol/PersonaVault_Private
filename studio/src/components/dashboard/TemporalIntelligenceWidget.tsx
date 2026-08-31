import React from 'react';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { useTemporalInsightsQuery } from '../../hooks/query/useTemporalInsightsQuery';
import styles from './TemporalIntelligenceWidget.module.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export const TemporalIntelligenceWidget: React.FC<{ timeRange: string }> = ({ timeRange }) => {
  const { data: metrics, isLoading, error } = useTemporalInsightsQuery(timeRange);

  if (isLoading) {
    return <div className={styles.loading}>Loading temporal intelligence...</div>;
  }

  if (error || !metrics) {
    return <div className={styles.error}>Failed to load temporal metrics</div>;
  }

  // Decision Velocity Chart
  const velocityData = {
    labels: metrics.trendData.dates,
    datasets: [
      {
        label: 'Decision Velocity',
        data: metrics.trendData.values,
        borderColor: '#818cf8',
        backgroundColor: 'rgba(129, 140, 248, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const velocityOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Decision Velocity Over Time',
        color: '#e0e0e0',
        font: {
          size: 14,
          weight: 'normal' as const
        }
      }
    },
    scales: {
      x: {
        ticks: { color: '#9ca3af' },
        grid: { color: 'rgba(255,255,255,0.05)' }
      },
      y: {
        beginAtZero: true,
        max: 1,
        ticks: { color: '#9ca3af' },
        grid: { color: 'rgba(255,255,255,0.05)' }
      }
    }
  };

  // Pattern Health Chart
  const healthData = {
    labels: ['Healthy', 'Decaying', 'Critical'],
    datasets: [
      {
        data: [
          metrics.patternHealth.healthy,
          metrics.patternHealth.decaying,
          metrics.patternHealth.critical
        ],
        backgroundColor: [
          '#22c55e',
          '#eab308',
          '#ef4444'
        ],
        borderColor: ['#1a1a2e', '#1a1a2e', '#1a1a2e'],
        borderWidth: 2
      }
    ]
  };

  const healthOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: '#e0e0e0'
        }
      },
      title: {
        display: true,
        text: 'Pattern Health Distribution',
        color: '#e0e0e0',
        font: {
          size: 14,
          weight: 'normal' as const
        }
      }
    }
  };

  return (
    <div className={styles.widget}>
      <div className={styles.header}>
        <h3>🕐 Temporal Intelligence</h3>
        <div className={styles.headerMetrics}>
          <div className={styles.metricBadge}>
            <span className={styles.metricLabel}>Velocity</span>
            <span className={styles.metricValue}>{metrics.velocity.toFixed(2)}</span>
          </div>
          <div className={styles.metricBadge}>
            <span className={styles.metricLabel}>Decay Rate</span>
            <span className={styles.metricValue}>{(metrics.decayRate * 100).toFixed(1)}%</span>
          </div>
          <div className={`${styles.metricBadge} ${metrics.agingPatterns > 0 ? styles.warning : ''}`}>
            <span className={styles.metricLabel}>Aging Patterns</span>
            <span className={styles.metricValue}>{metrics.agingPatterns}</span>
          </div>
        </div>
      </div>

      <div className={styles.grid}>
        <div className={styles.chartContainer}>
          <Line data={velocityData} options={velocityOptions} />
        </div>
        
        <div className={`${styles.chartContainer} ${styles.small}`}>
          <Doughnut data={healthData} options={healthOptions} />
        </div>
      </div>

      <div className={styles.footer}>
        <div className={styles.insight}>
          <span className={styles.insightIcon}>💡</span>
          <span className={styles.insightText}>
            {metrics.velocity > 0.7 && metrics.decayRate < 0.3
              ? 'System is learning efficiently. Temporal patterns are strengthening.'
              : metrics.velocity < 0.3 && metrics.decayRate > 0.6
              ? 'Pattern decay is outpacing learning. Consider reviewing older decisions.'
              : metrics.agingPatterns > 0
              ? `${metrics.agingPatterns} patterns need review. Action recommended.`
              : 'Temporal intelligence is stable. No immediate action required.'}
          </span>
        </div>
      </div>
    </div>
  );
};
