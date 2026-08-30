import { useEffect } from 'react';
import { useMCPStore } from '../store/mcpStore';

export const useMCP = () => {
  const { tools, integrations, isLoading, error, fetchTools, fetchIntegrations, callTool } = useMCPStore();

  useEffect(() => {
    fetchTools();
    fetchIntegrations();
  }, [fetchTools, fetchIntegrations]);

  return {
    tools,
    integrations,
    isLoading,
    error,
    callTool,
  };
};
