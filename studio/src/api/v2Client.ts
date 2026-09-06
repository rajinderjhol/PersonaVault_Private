// V2 API Client for PersonaVault Studio
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class V2ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE_URL;
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}/v2${path}`;
    
    console.log(`📡 V2 ${options.method || 'GET'}: ${url}`);
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // ✅ Use cookies instead of Bearer token
    });

    if (!response.ok) {
      console.error(`❌ V2 ${options.method || 'GET'} Error: ${response.status} at ${url}`);
      throw new Error(`API V2 Error: ${response.status}`);
    }

    return response.json();
  }

  async get<T>(path: string, options?: { params?: Record<string, any> }): Promise<T> {
    let url = path;
    if (options?.params) {
      const searchParams = new URLSearchParams();
      Object.entries(options.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, value.toString());
        }
      });
      url += `?${searchParams.toString()}`;
    }
    return this.request<T>(url, { method: 'GET' });
  }

  async post<T>(path: string, body: any): Promise<T> {
    return this.request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  async put<T>(path: string, body: any): Promise<T> {
    return this.request<T>(path, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }
  
  async patch<T>(path: string, body: any): Promise<T> {
    return this.request<T>(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  }

  async delete<T>(path: string): Promise<T> {
    return this.request<T>(path, { method: 'DELETE' });
  }
}

export const v2ApiClient = new V2ApiClient();
