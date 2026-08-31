// src/services/api.ts
const API_BASE_URL = '/api/v1';

export const api = {
  get: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
    return response.json();
  },
  post: async <T>(endpoint: string, data?: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
    return response.json();
  },
  put: async <T>(endpoint: string, data?: any): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
    return response.json();
  },
  delete: async <T>(endpoint: string): Promise<T> => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    });
    if (!response.ok) throw new Error(`API Error: ${response.status} ${response.statusText}`);
    return response.json();
  },
  // Add 'put' and 'delete' methods as needed
};

export const dashboardApi = {
  getStats: () => api.get('/dashboard/stats'),
  getDecisions: (params?: any) => api.get('/decisions' + (params ? `?${new URLSearchParams(params)}` : '')),
  getTrends: (timeframe?: string) => api.get(`/dashboard/trends?timeframe=${timeframe || 'week'}`),
  getPatterns: () => api.get('/patterns/recent'),
};

export default api;
