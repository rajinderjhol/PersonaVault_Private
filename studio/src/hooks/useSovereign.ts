import { useEffect } from 'react';
import { useSovereignStore } from '../store/sovereignStore';

export const useSovereign = () => {
  const { executionMode, airGapped, dataSovereigntyLevel, modeConfig, isLoading, error, fetchCurrentMode, setMode, toggleAirGapped, setSovereignty } = useSovereignStore();

  useEffect(() => {
    fetchCurrentMode();
  }, [fetchCurrentMode]);

  return {
    executionMode,
    airGapped,
    dataSovereigntyLevel,
    modeConfig,
    isLoading,
    error,
    setMode,
    toggleAirGapped,
    setSovereignty,
  };
};
