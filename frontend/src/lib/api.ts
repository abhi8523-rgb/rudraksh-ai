import { API_BASE_URL } from './constants';
import type { ApiResponse } from '@/types';

/* ════════════════════════════════════════════════════════════════
   Rudraksh AI — API Client
   Centralized fetch wrapper with JWT, error handling, base URL
   ════════════════════════════════════════════════════════════════ */

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('rudraksh_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return headers;
  }

  async get<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return { success: false, error: error.detail || 'Request failed' };
      }
      const data = await res.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  }

  async post<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers: this.getHeaders(),
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return { success: false, error: error.detail || 'Request failed' };
      }
      const data = await res.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  }

  async put<T>(endpoint: string, body?: unknown): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: this.getHeaders(),
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return { success: false, error: error.detail || 'Request failed' };
      }
      const data = await res.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'DELETE',
        headers: this.getHeaders(),
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return { success: false, error: error.detail || 'Request failed' };
      }
      const data = await res.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  }

  async upload<T>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    try {
      const headers: HeadersInit = {};
      if (typeof window !== 'undefined') {
        const token = localStorage.getItem('rudraksh_token');
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
      }
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        return { success: false, error: error.detail || 'Upload failed' };
      }
      const data = await res.json();
      return { success: true, data };
    } catch (err) {
      return { success: false, error: (err as Error).message };
    }
  }
}

export const api = new ApiClient(API_BASE_URL);
export default api;
