import React from 'react';
import { useMarketplaceQuery } from '../hooks/query/useMarketplaceQuery';
import { useInstallPackMutation } from '../hooks/mutation/useInstallPackMutation';

export const Marketplace: React.FC = () => {
  const { data, isLoading, error } = useMarketplaceQuery();
  const installMutation = useInstallPackMutation();

  if (isLoading) return <div>Loading Marketplace...</div>;
  if (error) return <div>Error loading Marketplace: {error instanceof Error ? error.message : 'Unknown error'}</div>;
  if (!data || !data.packs) return <div>No marketplace data available</div>;

  const handleInstall = (packId: string) => {
    installMutation.mutate(packId);
  };

  return (
    <div className="marketplace-container">
      <h1>Marketplace</h1>
      <div className="marketplace-grid">
        {Array.isArray(data.packs) && data.packs.map((item: any) => (
          <div key={item.id} className="marketplace-item" style={{ border: '1px solid #ccc', padding: '1rem', margin: '1rem' }}>
            <h3>{item.name}</h3>
            <p>{item.description}</p>
            {item.is_installed ? (
              <button disabled>Installed</button>
            ) : (
              <button onClick={() => handleInstall(item.id)} disabled={installMutation.isPending}>
                {installMutation.isPending ? 'Installing...' : 'Install'}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
