// API Client for PersonaVault Studio
const VITE_API_URL = import.meta.env.VITE_API_URL;
// If VITE_API_URL is provided, use it. Otherwise, use relative /api/v1 which is proxied by Vite.
const API_BASE_URL = VITE_API_URL ? VITE_API_URL.replace(/\/$/, '') : '/api/v1';

console.log('🔌 API Client using base:', API_BASE_URL);

export const apiClient = {
  get: async <T = any>(endpoint: string, options?: { params?: Record<string, any> }): Promise<T> => {
    try {
      // Ensure endpoint starts with / and doesn't duplicate v1
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const baseUrl = API_BASE_URL.startsWith('http') 
        ? API_BASE_URL 
        : `${window.location.origin}${API_BASE_URL}`;
      
      const url = new URL(`${baseUrl}${path}`);
      
      if (options?.params) {
        Object.entries(options.params).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            url.searchParams.append(key, value.toString());
          }
        });
      }
      
      const response = await fetch(url.toString(), {
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
  post: async <T = any>(endpoint: string, data?: any): Promise<T> => {
    try {
      const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
      const baseUrl = API_BASE_URL.startsWith('http') 
        ? API_BASE_URL 
        : `${window.location.origin}${API_BASE_URL}`;
        
      const response = await fetch(`${baseUrl}${path}`, {
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
};
export default apiClient;
