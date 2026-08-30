import React from 'react';
import { motion } from 'framer-motion';
import { useThermodynamicsStore } from '../../../../store/thermodynamicsStore';
import { Wind, Droplets, Snowflake, Sparkles } from 'lucide-react';

const ThermodynamicView: React.FC = () => {
  const { phases } = useThermodynamicsStore();

  return (
    <div style={{
      backgroundColor: 'var(--color-bg-secondary)',
      borderRadius: '16px',
      padding: '24px',
      border: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          Thermodynamic Memory Map
        </h2>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
          System Temperature: <span style={{ color: 'var(--color-gas)' }}>24°C (Stable)</span>
        </div>
      </div>

      <div style={{
        height: '240px',
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
        borderRadius: '12px',
        overflow: 'hidden',
        border: '1px solid var(--glass-border)'
      }}>
        <Layer 
          name="Gas (Working)" 
          color="var(--color-gas)" 
          percentage={phases.gas} 
          icon={<Wind size={14} />} 
          description="Transient context and IoT data"
        />
        <Layer 
          name="Liquid (Episodic)" 
          color="var(--color-liquid)" 
          percentage={phases.liquid} 
          icon={<Droplets size={14} />} 
          description="Interaction history and logs"
        />
        <Layer 
          name="Ice (Semantic)" 
          color="var(--color-ice)" 
          percentage={phases.ice} 
          icon={<Snowflake size={14} />} 
          description="Crystallized patterns"
        />
        <Layer 
          name="Snowflakes (Domain)" 
          color="#a5f3fc" 
          percentage={phases.snowflake} 
          icon={<Sparkles size={14} />} 
          description="Specialized domain variants"
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginTop: '10px' }}>
        <PhaseMetric label="Volatility" value="High" color="var(--color-gas)" />
        <PhaseMetric label="Durity" value="Medium" color="var(--color-liquid)" />
        <PhaseMetric label="Density" value="Extreme" color="var(--color-ice)" />
        <PhaseMetric label="Specificity" value="High" color="#a5f3fc" />
      </div>
    </div>
  );
};

const Layer: React.FC<{ name: string, color: string, percentage: number, icon: React.ReactNode, description: string }> = ({ name, color, percentage, icon, description }) => (
  <motion.div 
    initial={{ flex: 0 }}
    animate={{ flex: percentage }}
    style={{
      backgroundColor: `rgba(${parseInt(color.slice(1,3), 16)}, ${parseInt(color.slice(3,5), 16)}, ${parseInt(color.slice(5,7), 16)}, 0.15)`,
      borderLeft: `4px solid ${color}`,
      padding: '12px 16px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      position: 'relative',
      minHeight: '40px',
      transition: 'all 0.5s cubic-bezier(0.4, 0, 0.2, 1)'
    }}
  >
    <div style={{ display: 'flex', flexDirection: 'column', zIndex: 2 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '0.9rem', color: color }}>
        {icon} {name}
      </div>
      <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{description}</div>
    </div>
    <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-text-primary)', zIndex: 2 }}>
      {percentage}%
    </div>
    
    {/* Animated background pulse */}
    <motion.div 
      animate={{ opacity: [0.1, 0.3, 0.1] }}
      transition={{ repeat: Infinity, duration: 4 }}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: `linear-gradient(90deg, ${color}22 0%, transparent 100%)`,
        zIndex: 1
      }}
    />
  </motion.div>
);

const PhaseMetric: React.FC<{ label: string, value: string, color: string }> = ({ label, value, color }) => (
  <div style={{ textAlign: 'center' }}>
    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '4px' }}>{label}</div>
    <div style={{ fontSize: '0.9rem', fontWeight: 600, color: color }}>{value}</div>
  </div>
);

export default ThermodynamicView;
