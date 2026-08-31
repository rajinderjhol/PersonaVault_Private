import React from 'react';
import { useMarketplaceQuery } from '../hooks/query/useMarketplaceQuery';

export const Marketplace: React.FC = () => {
  const { data, isLoading, error } = useMarketplaceQuery();

  if (isLoading) return <div>Loading Marketplace...</div>;
  if (error) return <div>Error loading Marketplace: {error instanceof Error ? error.message : 'Unknown error'}</div>;
  if (!data || !data.packs) return <div>No marketplace data available</div>;

  return (
    <div className="marketplace-container">
      <h1>Marketplace</h1>
      <div className="marketplace-grid">
        {/* Render marketplace items from data.packs */}
        {Array.isArray(data.packs) && data.packs.map((item: any) => (
          <div key={item.id} className="marketplace-item" style={{ border: '1px solid #ccc', padding: '1rem', margin: '1rem' }}>
            <h3>{item.name}</h3>
            <p>{item.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
};
