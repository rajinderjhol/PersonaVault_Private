import { useEffect } from 'react';
import { usePackStore } from '../store/packStore';

export const usePacks = () => {
  const { packs, installedPacks, isLoading, error, fetchPacks, installPack, uninstallPack } = usePackStore();

  useEffect(() => {
    fetchPacks();
  }, [fetchPacks]);

  return {
    packs,
    installedPacks,
    isLoading,
    error,
    installPack,
    uninstallPack,
  };
};
