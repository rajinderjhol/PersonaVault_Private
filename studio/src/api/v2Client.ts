// V2 API Client for PersonaVault Studio
const V2_BASE_URL = '/v2';

import { ApiClient } from './client';

// Simple factory for creating V2 client based on existing ApiClient interface
// This keeps V2 calls isolated from V1 base URL logic
export const v2ApiClient: ApiClient = {
  get: async <T = any>(endpoint: string, options?: { params?: Record<string, any>; responseType?: 'stream' | 'json' }): Promise<T> => {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    // Use relative URL to let Vite/browser handle origin and proxying
    const url = new URL(`${V2_BASE_URL}${path}`, window.location.origin);
    
    if (options?.params) {
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.append(key, value.toString());
        }
      });
    }
    
    console.log(`📡 V2 GET: ${url.pathname}${url.search}`);
    const response = await fetch(url.toString(), {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    
    if (!response.ok) {
      console.error(`❌ V2 GET Error: ${response.status} ${response.statusText} at ${url.pathname}`);
      throw new Error(`API V2 Error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  },
  post: async <T = any>(endpoint: string, data?: any): Promise<T> => {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${V2_BASE_URL}${path}`, window.location.origin);
    
    console.log(`📡 V2 POST: ${url.pathname}`, data);
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) {
      console.error(`❌ V2 POST Error: ${response.status} ${response.statusText} at ${url.pathname}`);
      throw new Error(`API V2 Error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  },
  put: async <T = any>(endpoint: string, data?: any): Promise<T> => {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${V2_BASE_URL}${path}`, window.location.origin);
    
    const response = await fetch(url.toString(), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) throw new Error(`API V2 Error: ${response.status} ${response.statusText}`);
    return await response.json();
  },
  patch: async <T = any>(endpoint: string, data?: any): Promise<T> => {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${V2_BASE_URL}${path}`, window.location.origin);
    
    const response = await fetch(url.toString(), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: data ? JSON.stringify(data) : undefined,
    });
    
    if (!response.ok) throw new Error(`API V2 Error: ${response.status} ${response.statusText}`);
    return await response.json();
  },
  delete: async <T = any>(endpoint: string): Promise<T> => {
    const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = new URL(`${V2_BASE_URL}${path}`, window.location.origin);
    
    const response = await fetch(url.toString(), {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    
    if (!response.ok) throw new Error(`API V2 Error: ${response.status} ${response.statusText}`);
    return await response.json();
  },
};
