import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useAuth } from '../context/AuthContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Autocomplete } from '../components/Autocomplete.jsx';
import { useToast } from '../components/Toast.jsx';

function MembersPanel({ groupId }) {
  const toast = useToast();
  const { user } = useAuth();
  const members = useFetch(() => api.prediction(`/groups/${groupId}/members`), [groupId]);
  const allUsers = useFetch(() => api.prediction('/admin/users'), []);
  const [username, setUsername] = useState('');
  const [busy, setBusy] = useState(false);

  const memberIds = new Set((members.data || []).map((m) => m.user_id));
  const candidates = (allUsers.data || [])
    .filter((u) => !memberIds.has(u.id))
    .map((u) => ({ value: u.username, label: `${u.display_name} (${u.username})` }));

  async function add() {
    if (!username) return;
    setBusy(true);
    try {
      await api.prediction(`/admin/groups/${groupId}/members`, {
        method: 'POST',
        body: { username },
      });
      toast.success('Đã thêm thành viên');
      setUsername('');
      members.reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function removeMember(userId, displayName) {
    if (!window.confirm(`Xóa ${displayName} khỏi group?`)) return;
    try {
      await api.prediction(`/admin/groups/${groupId}/members/${userId}`, {
        method: 'DELETE',
      });
      toast.success(`Đã xóa ${displayName}`);
      members.reload();
    } catch (err) {
      toast.error(err.message);
    }
  }

  const isAdmin = Boolean(user?.is_admin);

  const columns = [
    { key: 'display_name', label: 'Thành viên', render: (m) => <strong>{m.display_name}</strong> },
    { key: 'username', label: 'Đăng nhập', render: (m) => <span className="mono">{m.username}</span> },
    ...(isAdmin
      ? [{
          key: 'actions',
          label: '',
          align: 'right',
          render: (m) => (
            <button
              className="btn btn-secondary btn-sm"
              onClick={(e) => { e.stopPropagation(); removeMember(m.user_id, m.display_name); }}
            >
              Xóa
            </button>
          ),
        }]
      : []),
  ];

  return (
    <div className="panel">
      <div className="panel-head"><h3>Thành viên</h3></div>
      {isAdmin && (
        <div className="inline-form" style={{ marginBottom: 14 }}>
          <div style={{ flex: 1, minWidth: 200 }}>
            <Autocomplete
              options={candidates}
              value={username}
              onChange={setUsername}
              placeholder="Tìm người dùng để thêm…"
            />
          </div>
          <button className="btn btn-primary" onClick={add} disabled={busy || !username}>
            Thêm
          </button>
        </div>
      )}
      {members.loading
        ? <div className="loading">Đang tải thành viên…</div>
        : <DataTable columns={columns} rows={members.data} empty="Group chưa có thành viên" />
      }
    </div>
  );
}

export function GroupSettings() {
  const { groupId } = useParams();
  const { groups } = useGroups();
  const group = groups.find((g) => g.id === groupId);

  return (
    <div>
      <div className="section-title">{group ? group.name : groupId}</div>
      <MembersPanel groupId={groupId} />
    </div>
  );
}
