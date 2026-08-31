import { api } from './api';

export const apiExplorerService = {
  callEndpoint: (method: 'GET' | 'POST' | 'PUT' | 'DELETE', path: string, data?: any) => {
    switch (method) {
      case 'GET': return api.get(path);
      case 'POST': return api.post(path, data);
      case 'PUT': return api.put(path, data);
      case 'DELETE': return api.delete(path);
      default: throw new Error(`Unsupported method: ${method}`);
    }
  },
};
