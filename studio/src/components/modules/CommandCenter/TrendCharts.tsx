import React, { useEffect, useRef } from 'react';
import { useTrends } from '../../../hooks/useTrends';

export const TrendCharts: React.FC = () => {
  const { trends, domains, isLoading, fetchTrends } = useTrends();
  const chartRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchTrends();
  }, []);

  useEffect(() => {
    if (trends.length > 0 && chartRef.current) {
      drawTrendChart();
    }
  }, [trends]);

  const drawTrendChart = () => {
    const canvas = chartRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.parentElement?.getBoundingClientRect();
    if (rect) {
      canvas.width = rect.width - 40;
      canvas.height = rect.height - 40;
    }

    const padding = { top: 20, right: 20, bottom: 30, left: 50 };
    const chartWidth = canvas.width - padding.left - padding.right;
    const chartHeight = canvas.height - padding.top - padding.bottom;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw grid
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 0.5;
    for (let i = 0; i < 5; i++) {
      const y = padding.top + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(canvas.width - padding.right, y);
      ctx.stroke();
    }

    // Draw axes labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '10px system-ui, sans-serif';
    ctx.textAlign = 'center';
    
    // Use the labels from the first domain if available
    if (trends.length > 0) {
      trends[0].labels.forEach((label, index) => {
        const x = padding.left + (chartWidth / (trends[0].labels.length - 1)) * index;
        ctx.fillText(label, x, canvas.height - 5);
      });
    }

    // Draw trends
    const colors = ['#3b82f6', '#10b981', '#f472b6', '#f59e0b', '#8b5cf6'];
    trends.forEach((trend, domainIndex) => {
      const color = colors[domainIndex % colors.length];
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;

      ctx.beginPath();
      trend.values.forEach((value: number, index: number) => {
        const x = padding.left + (chartWidth / (trend.values.length - 1)) * index;
        const y = padding.top + chartHeight - (value / 100) * chartHeight;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Draw points
      trend.values.forEach((value: number, index: number) => {
        const x = padding.left + (chartWidth / (trend.values.length - 1)) * index;
        const y = padding.top + chartHeight - (value / 100) * chartHeight;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
      });
    });

    // Draw legend
    let legendX = padding.left + 10;
    const legendY = padding.top + 10;
    ctx.font = '11px system-ui, sans-serif';
    trends.forEach((trend, index) => {
      const color = colors[index % colors.length];
      ctx.fillStyle = color;
      ctx.fillRect(legendX, legendY, 12, 12);
      ctx.fillStyle = '#0f172a';
      ctx.textAlign = 'left';
      ctx.fillText(trend.name, legendX + 16, legendY + 10);
      legendX += ctx.measureText(trend.name).width + 30;
    });

    // Draw title
    ctx.fillStyle = '#0f172a';
    ctx.font = '14px system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Confidence Trends by Domain', canvas.width / 2, 15);
  };

  if (isLoading) {
    return <div className="trends-loading">Loading trends...</div>;
  }

  return (
    <div className="trend-charts">
      <div className="trends-header">
        <h4>📊 Confidence Trends</h4>
        <div className="trends-controls">
          <select>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </select>
        </div>
      </div>
      <div className="trends-canvas-container">
        <canvas ref={chartRef} />
      </div>
    </div>
  );
};
