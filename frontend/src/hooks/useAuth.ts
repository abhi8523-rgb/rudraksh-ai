'use client';

import { useState, useCallback, useEffect } from 'react';
import type { AuthState } from '@/types';
import api from '@/lib/api';

/* ════════════════════════════════════════════════════════════════
   useAuth — Authentication state hook
   ════════════════════════════════════════════════════════════════ */

export function useAuth() {
  const [auth, setAuth] = useState<AuthState>({
    isAuthenticated: false,
    token: null,
    expiresAt: null,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('rudraksh_token');
    const expiresAt = localStorage.getItem('rudraksh_token_expires');
    if (token && expiresAt) {
      const expiry = parseInt(expiresAt, 10);
      if (Date.now() < expiry) {
        setAuth({ isAuthenticated: true, token, expiresAt: expiry });
      } else {
        localStorage.removeItem('rudraksh_token');
        localStorage.removeItem('rudraksh_token_expires');
      }
    }
    setIsLoading(false);
  }, []);

  const login = useCallback(async (passphrase: string): Promise<boolean> => {
    setIsLoading(true);
    try {
      const res = await api.post<{ token: string; expires_at: number }>('/api/auth/login', {
        passphrase,
      });
      if (res.success && res.data) {
        const { token, expires_at } = res.data;
        localStorage.setItem('rudraksh_token', token);
        localStorage.setItem('rudraksh_token_expires', expires_at.toString());
        setAuth({ isAuthenticated: true, token, expiresAt: expires_at });
        setIsLoading(false);
        return true;
      }
      setIsLoading(false);
      return false;
    } catch {
      setIsLoading(false);
      return false;
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('rudraksh_token');
    localStorage.removeItem('rudraksh_token_expires');
    setAuth({ isAuthenticated: false, token: null, expiresAt: null });
  }, []);

  return {
    ...auth,
    isLoading,
    login,
    logout,
  };
}
