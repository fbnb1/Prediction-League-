import { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { api } from '../api/client.js';

const AuthContext = createContext(null);

function loadUser() {
  const raw = localStorage.getItem('user');
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadUser);

  const persist = useCallback((token, payload) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(payload));
    setUser(payload);
  }, []);

  const fromToken = useCallback(
    (data) =>
      persist(data.access_token, {
        id: data.user_id,
        display_name: data.display_name,
        is_admin: Boolean(data.is_admin),
      }),
    [persist],
  );

  const login = useCallback(
    async (username, password) => {
      const data = await api.prediction('/auth/login', {
        method: 'POST',
        auth: false,
        body: { username, password },
      });
      fromToken(data);
    },
    [fromToken],
  );

  const register = useCallback(
    async (username, password) => {
      const data = await api.prediction('/auth/register', {
        method: 'POST',
        auth: false,
        body: { username, password },
      });
      fromToken(data);
    },
    [fromToken],
  );

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('selectedGroupId');
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, login, register, logout }),
    [user, login, register, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
