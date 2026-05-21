import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Modal } from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';

function PasswordModal({ user, onClose }) {
  const toast = useToast();
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.prediction(`/admin/users/${user.id}/password`, {
        method: 'PUT',
        body: { new_password: password },
      });
      toast.success(`Đã đổi mật khẩu cho ${user.display_name}`);
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title={`Đổi mật khẩu — ${user.display_name}`} onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Mật khẩu mới</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Đang lưu…' : 'Cập nhật'}
        </button>
      </form>
    </Modal>
  );
}

function CreateGroupModal({ onClose, onCreated }) {
  const toast = useToast();
  const [name, setName] = useState('');
  const [betType, setBetType] = useState('EUROPEAN');
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await api.prediction('/admin/groups', {
        method: 'POST',
        body: { name: name.trim(), bet_type: betType },
      });
      toast.success(`Đã tạo group "${name}"`);
      onCreated();
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Modal title="Thêm group mới" onClose={onClose}>
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Tên group</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label className="field">
          <span>Loại kèo</span>
          <select value={betType} onChange={(e) => setBetType(e.target.value)}>
            <option value="EUROPEAN">Châu Âu (1X2)</option>
            <option value="ASIAN">Châu Á (handicap)</option>
          </select>
        </label>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? 'Đang tạo…' : 'Tạo group'}
        </button>
      </form>
    </Modal>
  );
}

export function Admin() {
  const navigate = useNavigate();
  const { groups, refresh: refreshGroups } = useGroups();
  const users = useFetch(() => api.prediction('/admin/users'), []);
  const [pwUser, setPwUser] = useState(null);
  const [creating, setCreating] = useState(false);

  const userColumns = [
    { key: 'display_name', label: 'Tên hiển thị', sortable: true, render: (u) => <strong>{u.display_name}</strong> },
    { key: 'username', label: 'Đăng nhập', sortable: true, render: (u) => <span className="mono">{u.username}</span> },
    {
      key: 'is_admin',
      label: 'Vai trò',
      render: (u) =>
        u.is_admin ? <span className="badge admin">Admin</span> : <span className="hint">Người chơi</span>,
    },
    {
      key: 'actions',
      label: '',
      align: 'right',
      render: (u) => (
        <button
          className="btn btn-secondary btn-sm"
          onClick={(e) => {
            e.stopPropagation();
            setPwUser(u);
          }}
        >
          Đổi mật khẩu
        </button>
      ),
    },
  ];

  const groupColumns = [
    { key: 'name', label: 'Group', sortable: true, render: (g) => <strong>{g.name}</strong> },
    {
      key: 'bet_type',
      label: 'Loại kèo',
      render: (g) => (
        <span className={`badge ${g.bet_type.toLowerCase()}`}>{g.bet_type}</span>
      ),
    },
    { key: 'id', label: 'Mã', render: (g) => <span className="mono">{g.id}</span> },
  ];

  return (
    <div>
      <div className="section-title">Người dùng</div>
      {users.loading ? (
        <div className="loading">Đang tải người dùng…</div>
      ) : users.error ? (
        <div className="loading">Không tải được: {users.error.message}</div>
      ) : (
        <DataTable columns={userColumns} rows={users.data} />
      )}

      <div className="row-between" style={{ margin: '28px 0 14px' }}>
        <div className="section-title" style={{ margin: 0 }}>
          Group
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setCreating(true)}>
          + Thêm group
        </button>
      </div>
      <DataTable
        columns={groupColumns}
        rows={groups}
        onRowClick={(g) => navigate(`/admin/groups/${g.id}`)}
        empty="Chưa có group nào"
      />

      {pwUser && <PasswordModal user={pwUser} onClose={() => setPwUser(null)} />}
      {creating && (
        <CreateGroupModal onClose={() => setCreating(false)} onCreated={refreshGroups} />
      )}
    </div>
  );
}
