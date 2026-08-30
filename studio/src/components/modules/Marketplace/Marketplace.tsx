import React from 'react';
import { useMarketplaceStore } from '../../../store/marketplaceStore';
import { ShoppingBag, Download, Trash2, Star, Users, Info, Settings, BarChart2 } from 'lucide-react';
import PackSigning from './PackSigning';

const Marketplace: React.FC = () => {
  const { availablePacks, installPack, uninstallPack } = useMarketplaceStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ShoppingBag size={24} color="var(--color-gas)" /> Intelligence Marketplace
        </h2>
        <div style={{ display: 'flex', gap: '12px' }}>
          <input 
            type="text" 
            placeholder="Search packs..." 
            style={{ 
              backgroundColor: 'var(--color-bg-secondary)', 
              border: '1px solid var(--glass-border)', 
              borderRadius: '8px', 
              padding: '8px 16px',
              color: 'white',
              outline: 'none'
            }} 
          />
          <button style={{ backgroundColor: 'var(--color-bg-tertiary)', color: 'white', border: '1px solid var(--glass-border)', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>
            Filter
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
          {availablePacks.map(pack => (
            <PackCard 
              key={pack.id} 
              pack={pack} 
              onInstall={() => installPack(pack.id)} 
              onUninstall={() => uninstallPack(pack.id)} 
            />
          ))}
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <PackSigning />
          
          <div style={{ backgroundColor: 'var(--color-bg-secondary)', padding: '24px', borderRadius: '16px', border: '1px solid var(--glass-border)' }}>
            <h3 style={{ fontSize: '0.9rem', textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: '16px' }}>Marketplace Policy</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <PolicyItem label="Automatic Updates" active />
              <PolicyItem label="Strict Signature Check" active />
              <PolicyItem label="Telemetry Opt-Out" active={false} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const PackCard: React.FC<{ pack: any, onInstall: () => void, onUninstall: () => void }> = ({ pack, onInstall, onUninstall }) => (
  <div style={{ 
    backgroundColor: 'var(--color-bg-secondary)', 
    borderRadius: '16px', 
    border: '1px solid var(--glass-border)',
    overflow: 'hidden',
    display: 'flex',
    flexDirection: 'column',
    transition: 'transform 0.2s ease, border-color 0.2s ease',
    cursor: 'default'
  }}
  onMouseEnter={(e) => {
    e.currentTarget.style.transform = 'translateY(-4px)';
    e.currentTarget.style.borderColor = 'var(--color-gas)';
  }}
  onMouseLeave={(e) => {
    e.currentTarget.style.transform = 'translateY(0)';
    e.currentTarget.style.borderColor = 'var(--glass-border)';
  }}
  >
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', flex: 1 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--color-gas)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{pack.domain}</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-text-primary)' }}>{pack.name}</div>
        </div>
        <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Star size={14} fill="var(--color-warning)" color="var(--color-warning)" /> {pack.rating}
        </div>
      </div>
      
      <p style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
        {pack.description}
      </p>

      <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Users size={12} /> {pack.installCount.toLocaleString()}</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Info size={12} /> v{pack.version}</div>
      </div>

      {pack.isInstalled && pack.metrics && (
        <div style={{ 
          marginTop: '8px',
          padding: '12px', 
          backgroundColor: 'rgba(0, 242, 255, 0.05)', 
          borderRadius: '8px', 
          border: '1px solid rgba(0, 242, 255, 0.1)',
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '12px'
        }}>
          <MetricItem label="Events" value={pack.metrics.events} />
          <MetricItem label="Conf." value={`${(pack.metrics.confidence * 100).toFixed(0)}%`} />
          <MetricItem label="Patterns" value={pack.metrics.patterns} />
        </div>
      )}
    </div>

    <div style={{ padding: '16px 24px', backgroundColor: 'rgba(30, 41, 59, 0.5)', borderTop: '1px solid var(--glass-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', gap: '12px' }}>
        <button style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}><Settings size={18} /></button>
        <button style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}><BarChart2 size={18} /></button>
      </div>
      
      {pack.isInstalled ? (
        <button 
          onClick={onUninstall}
          style={{ backgroundColor: 'transparent', color: 'var(--color-error)', border: '1px solid var(--color-error)', padding: '6px 16px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Trash2 size={14} /> Uninstall
        </button>
      ) : (
        <button 
          onClick={onInstall}
          style={{ backgroundColor: 'var(--color-gas)', color: 'var(--color-bg-primary)', border: 'none', padding: '6px 16px', borderRadius: '6px', fontSize: '0.85rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
        >
          <Download size={14} /> Install Pack
        </button>
      )}
    </div>
  </div>
);

const MetricItem: React.FC<{ label: string, value: any }> = ({ label, value }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
    <div style={{ fontSize: '0.6rem', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{label}</div>
    <div style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--color-gas)' }}>{value}</div>
  </div>
);

const PolicyItem: React.FC<{ label: string, active: boolean }> = ({ label, active }) => (
  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)' }}>{label}</span>
    <div style={{ 
      width: '32px', 
      height: '18px', 
      borderRadius: '9px', 
      backgroundColor: active ? 'var(--color-success)' : 'var(--color-bg-tertiary)',
      position: 'relative',
      cursor: 'pointer',
      border: '1px solid var(--glass-border)'
    }}>
      <div style={{ 
        width: '12px', 
        height: '12px', 
        borderRadius: '50%', 
        backgroundColor: 'white', 
        position: 'absolute',
        top: '2px',
        left: active ? '17px' : '2px',
        transition: 'left 0.2s ease'
      }} />
    </div>
  </div>
);

export default Marketplace;
