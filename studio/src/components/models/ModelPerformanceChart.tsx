import React from 'react';
import styles from './ModelPerformanceChart.module.css';

interface ChartData {
  label: string;
  value: number;
  color?: string;
}

interface ModelPerformanceChartProps {
  data?: ChartData[];
  title: string;
  type: 'confidence' | 'latency';
}

export const ModelPerformanceChart: React.FC<ModelPerformanceChartProps> = ({
  data = [],
  title,
  type,
}) => {
  if (!data || data.length === 0) return <div className={styles.container}>No data for {title}</div>;

  const maxValue = Math.max(...data.map(d => d.value));
  const isConfidence = type === 'confidence';

  return (
    <div className={styles.container}>
      <h4 className={styles.chartTitle}>{title}</h4>
      <div className={styles.chart}>
        {data.map((item, index) => (
          <div key={index} className={styles.barContainer}>
            <div className={styles.barLabel}>{item.label}</div>
            <div 
              className={styles.bar}
              style={{
                height: `${(item.value / maxValue) * 100}%`,
                backgroundColor: isConfidence 
                  ? `hsl(210, ${item.value}%, 50%)`
                  : `hsl(340, ${100 - (item.value / maxValue) * 100}%, 50%)`,
                transition: 'height 0.6s ease',
              }}
            >
              <span className={styles.barValue}>
                {isConfidence ? `${item.value}%` : `${item.value}ms`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
