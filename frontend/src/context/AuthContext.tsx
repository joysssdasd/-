import { createContext, useCallback, useEffect, useMemo, useState } from 'react';
import api from '../api';

export type UserProfile = {
  id: number;
  phone: string;
  wechat_id: string;
  invite_code?: string | null;
};

type AuthContextValue = {
  token: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState<UserProfile | null>(null);

  const fetchUser = useCallback(async (overrideToken?: string | null) => {
    const activeToken = overrideToken ?? token;
    if (!activeToken) {
      setUser(null);
      return;
    }
    try {
      const { data } = await api.get('/api/v1/users/me', {
        headers: { Authorization: `Bearer ${activeToken}` }
      });
      setUser(data);
    } catch (error) {
      console.error('Failed to load user profile', error);
      setUser(null);
    }
  }, [token]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const login = useCallback(async (nextToken: string) => {
    localStorage.setItem('access_token', nextToken);
    setToken(nextToken);
    await fetchUser(nextToken);
  }, [fetchUser]);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const value = useMemo(
    () => ({
      token,
      user,
      isAuthenticated: Boolean(token),
      login,
      logout,
      refreshUser
    }),
    [token, user, login, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
