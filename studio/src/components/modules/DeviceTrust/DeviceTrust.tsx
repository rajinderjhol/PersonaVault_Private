import React from 'react';
import { useDeviceStore } from '../../../store/deviceStore';
import { Shield, Smartphone, Laptop, Cpu, Radio, RefreshCw, ShieldCheck, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

const DeviceTrust: React.FC = () => {
  const { devices } = useDeviceStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '24px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Shield size={20} color="var(--color-success)" /> Trusted Device Map
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {devices.map(device => (
              <DeviceCard key={device.id} device={device} />
            ))}
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Sync Monitor */}
          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <RefreshCw size={16} /> Edge Sync Status
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <SyncItem label="Global Pattern Sync" progress={100} />
              <SyncItem label="Local Ephemeris" progress={85} />
              <SyncItem label="Identity Merging" progress={42} />
            </div>
          </div>

          {/* Trust Policies */}
          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px' }}>Trust Constraints</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <PolicyToggle label="Biometric Mandatory" active />
              <PolicyToggle label="Geo-Fencing (Home)" active={false} />
              <PolicyToggle label="Hardware Attestation" active />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const DeviceCard: React.FC<{ device: any }> = ({ device }) => {
  const Icon = device.type === 'mobile' ? Smartphone : device.type === 'desktop' ? Laptop : device.type === 'edge' ? Cpu : Radio;
  const isHighTrust = device.trustScore >= 0.8;

  return (
    <div style={{ 
      backgroundColor: 'var(--color-bg-secondary)', 
      padding: '24px', 
      borderRadius: '16px', 
      border: '1px solid var(--glass-border)',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ 
          width: '48px', 
          height: '48px', 
          borderRadius: '12px', 
          backgroundColor: 'var(--color-bg-tertiary)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: device.status === 'online' ? 'var(--color-gas)' : 'var(--color-text-muted)'
        }}>
          <Icon size={24} />
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ 
            fontSize: '0.7rem', 
            textTransform: 'uppercase', 
            color: device.status === 'online' ? 'var(--color-success)' : 'var(--color-text-muted)',
            fontWeight: 700
          }}>
            {device.status}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>Seen {new Date(device.lastSeen).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
      </div>

      <div>
        <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--color-text-primary)' }}>{device.name}</div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>ID: {device.id.padStart(6, '0')}</div>
      </div>

      <div style={{ marginTop: '4px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', alignItems: 'center' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
            {isHighTrust ? <ShieldCheck size={14} color="var(--color-success)" /> : <ShieldAlert size={14} color="var(--color-warning)" />}
            Trust Score
          </div>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: isHighTrust ? 'var(--color-success)' : 'var(--color-warning)' }}>
            {(device.trustScore * 100).toFixed(0)}%
          </div>
        </div>
        <div style={{ height: '6px', backgroundColor: 'var(--color-bg-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${device.trustScore * 100}%` }}
            style={{ height: '100%', backgroundColor: isHighTrust ? 'var(--color-success)' : 'var(--color-warning)' }} 
          />
        </div>
      </div>
      
      {device.syncProgress < 100 && (
        <div style={{ fontSize: '0.75rem', color: 'var(--color-gas)', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <RefreshCw size={12} className="animate-spin" /> Syncing: {device.syncProgress}%
        </div>
      )}
    </div>
  );
};

const SyncItem: React.FC<{ label: string, progress: number }> = ({ label, progress }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
      <span style={{ color: 'var(--color-text-secondary)' }}>{label}</span>
      <span style={{ color: 'var(--color-text-primary)', fontWeight: 600 }}>{progress}%</span>
    </div>
    <div style={{ height: '4px', backgroundColor: 'var(--color-bg-tertiary)', borderRadius: '2px', overflow: 'hidden' }}>
      <div style={{ width: `${progress}%`, height: '100%', backgroundColor: progress === 100 ? 'var(--color-success)' : 'var(--color-gas)' }} />
    </div>
  </div>
);

const PolicyToggle: React.FC<{ label: string, active: boolean }> = ({ label, active }) => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'space-between', 
    alignItems: 'center',
    padding: '12px',
    backgroundColor: 'var(--color-bg-tertiary)',
    borderRadius: '8px',
    border: '1px solid var(--glass-border)'
  }}>
    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-primary)' }}>{label}</span>
    <div style={{ 
      width: '32px', 
      height: '18px', 
      borderRadius: '9px', 
      backgroundColor: active ? 'var(--color-success)' : 'var(--color-text-muted)',
      position: 'relative',
      cursor: 'pointer'
    }}>
      <div style={{ 
        width: '14px', 
        height: '14px', 
        borderRadius: '50%', 
        backgroundColor: 'white', 
        position: 'absolute',
        top: '2px',
        left: active ? '16px' : '2px',
        transition: 'left 0.2s ease'
      }} />
    </div>
  </div>
);

export default DeviceTrust;
