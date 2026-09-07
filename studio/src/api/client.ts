// API Client for PersonaVault Studio
const VITE_API_URL = import.meta.env.VITE_API_URL;
// If VITE_API_URL is provided, use it. Otherwise, use relative /api/v1 which is proxied by Vite.
const API_BASE_URL = VITE_API_URL ? VITE_API_URL.replace(/\/$/, '') : '/api/v1';

console.log('🔌 API Client VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('🔌 API Client using base:', API_BASE_URL);

export interface ApiClient {
  get: <T = any>(endpoint: string, options?: { params?: Record<string, any>; responseType?: 'stream' | 'json' }) => Promise<T>;
  post: <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }) => Promise<T>;
  put: <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }) => Promise<T>;
  patch: <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }) => Promise<T>;
  delete: <T = any>(endpoint: string, options?: { responseType?: 'stream' | 'json' }) => Promise<T>;
}

export const apiClient: ApiClient = {
  get: async <T = any>(endpoint: string, options?: { params?: Record<string, any>; responseType?: 'stream' | 'json' }): Promise<T> => {
    try {
      // Ensure endpoint starts with /
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      
      // Construct URL: API_BASE_URL (if absolute) + path, or just path if relative
      const url = API_BASE_URL.startsWith('http') 
        ? `${API_BASE_URL}${path}`
        : `${API_BASE_URL}${path}`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      
      if (!response.ok) {
        if (response.status !== 401) {
          console.error('API Error:', response.status, response.statusText);
        }
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      // Only log if it's not a 401
      if (!(error instanceof Error) || !error.message.includes('401')) {
        console.error('API GET error:', error);
      }
      throw error;
    }
  },
  post: async <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }): Promise<T> => {
    try {
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = API_BASE_URL.startsWith('http') 
        ? `${API_BASE_URL}${path}`
        : `${API_BASE_URL}${path}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: data ? JSON.stringify(data) : undefined,
      });
      
      if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('API POST error:', error);
      throw error;
    }
  },
  put: async <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }): Promise<T> => {
    try {
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = API_BASE_URL.startsWith('http') 
        ? `${API_BASE_URL}${path}`
        : `${API_BASE_URL}${path}`;
      const response = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: data ? JSON.stringify(data) : undefined,
      });
      
      if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('API PUT error:', error);
      throw error;
    }
  },
  patch: async <T = any>(endpoint: string, data?: any, options?: { responseType?: 'stream' | 'json' }): Promise<T> => {
    try {
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = API_BASE_URL.startsWith('http') 
        ? `${API_BASE_URL}${path}`
        : `${API_BASE_URL}${path}`;
      const response = await fetch(url, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: data ? JSON.stringify(data) : undefined,
      });
      
      if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('API PATCH error:', error);
      throw error;
    }
  },
  delete: async <T = any>(endpoint: string, options?: { responseType?: 'stream' | 'json' }): Promise<T> => {
    try {
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const url = API_BASE_URL.startsWith('http') 
        ? `${API_BASE_URL}${path}`
        : `${API_BASE_URL}${path}`;
      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      
      if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
      return await response.json();
    } catch (error) {
      console.error('API DELETE error:', error);
      throw error;
    }
  },
};
export default apiClient;

