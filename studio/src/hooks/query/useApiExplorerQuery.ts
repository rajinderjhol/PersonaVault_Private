import { useMutation } from '@tanstack/react-query';
import { apiExplorerService } from '../../services/apiExplorerService';

export const useApiExplorerMutation = () => {
  return useMutation({
    mutationFn: ({ method, path, data }: { method: 'GET' | 'POST' | 'PUT' | 'DELETE'; path: string; data?: any }) => 
      apiExplorerService.callEndpoint(method, path, data),
  });
};
