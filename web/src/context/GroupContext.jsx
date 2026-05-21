import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { api } from '../api/client.js';
import { useAuth } from './AuthContext.jsx';

const GroupContext = createContext(null);

export function GroupProvider({ children }) {
  const { user } = useAuth();
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState(
    () => localStorage.getItem('selectedGroupId') || '',
  );
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!user) {
      setGroups([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const list = await api.prediction('/groups');
      setGroups(list);
      setSelectedGroupId((current) => {
        if (current && list.some((g) => g.id === current)) return current;
        return list[0]?.id || '';
      });
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const selectGroup = useCallback((id) => {
    setSelectedGroupId(id);
    localStorage.setItem('selectedGroupId', id);
  }, []);

  const selectedGroup = useMemo(
    () => groups.find((g) => g.id === selectedGroupId) || null,
    [groups, selectedGroupId],
  );

  const value = useMemo(
    () => ({ groups, selectedGroupId, selectedGroup, selectGroup, loading, refresh }),
    [groups, selectedGroupId, selectedGroup, selectGroup, loading, refresh],
  );
  return <GroupContext.Provider value={value}>{children}</GroupContext.Provider>;
}

export function useGroups() {
  const ctx = useContext(GroupContext);
  if (!ctx) throw new Error('useGroups must be used within GroupProvider');
  return ctx;
}
