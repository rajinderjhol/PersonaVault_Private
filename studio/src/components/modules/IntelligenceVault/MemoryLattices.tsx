import React, { useEffect, useRef } from 'react';
import { useMemoryLattices } from '../../../hooks/useMemoryLattices';

export const MemoryLattices: React.FC = () => {
  const { nodes, edges, isLoading, fetchLattices } = useMemoryLattices();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchLattices();
  }, []);

  useEffect(() => {
    if (nodes.length > 0 && canvasRef.current) {
      drawLattice();
    }
  }, [nodes, edges]);

  const drawLattice = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.parentElement?.getBoundingClientRect();
    if (rect) {
      canvas.width = rect.width;
      canvas.height = rect.height;
    }

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw edges
    edges.forEach(edge => {
      const source = nodes.find(n => n.id === edge.source);
      const target = nodes.find(n => n.id === edge.target);
      if (source && target) {
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = edge.color || '#3b82f6';
        ctx.lineWidth = edge.weight || 1;
        ctx.stroke();
      }
    });

    // Draw nodes
    nodes.forEach(node => {
      // Node circle
      const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.radius);
      gradient.addColorStop(0, node.color || '#60a5fa');
      gradient.addColorStop(1, node.color || '#3b82f6');
      ctx.beginPath();
      ctx.arc(node.x, node.y, node.radius || 20, 0, Math.PI * 2);
      ctx.fillStyle = gradient;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Node label
      ctx.fillStyle = '#ffffff';
      ctx.font = '12px system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label, node.x, node.y);

      // Node glow effect (for crystallized nodes)
      if (node.isCrystallized) {
        ctx.shadowColor = '#f472b6';
        ctx.shadowBlur = 20;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius + 5, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(244, 114, 182, 0.2)';
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    });
  };

  if (isLoading) {
    return <div className="lattices-loading">Loading memory lattices...</div>;
  }

  return (
    <div className="memory-lattices">
      <div className="lattices-header">
        <h3>🕸️ Memory Lattices</h3>
        <div className="lattices-legend">
          <span className="legend-item">
            <span className="legend-dot ice"></span> Ice (Crystallized)
          </span>
          <span className="legend-item">
            <span className="legend-dot liquid"></span> Liquid (Episodic)
          </span>
          <span className="legend-item">
            <span className="legend-dot gas"></span> Gas (Working)
          </span>
        </div>
      </div>
      <div className="lattices-canvas-container">
        <canvas ref={canvasRef} />
      </div>
      <div className="lattices-stats">
        <span>🧊 {nodes.filter(n => n.isCrystallized).length} Crystallized</span>
        <span>💧 {nodes.filter(n => n.type === 'liquid').length} Liquid</span>
        <span>💨 {nodes.filter(n => n.type === 'gas').length} Gas</span>
        <span>🔗 {edges.length} Connections</span>
      </div>
    </div>
  );
};
