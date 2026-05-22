import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Modal } from '../components/Modal.jsx';
import { useToast } from '../components/Toast.jsx';
import { formatDateTime } from '../utils/format.js';

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

function OddsManager() {
  const toast = useToast();
  const fixtures = useFetch(() => api.fixture('/fixtures'), []);
  const [matchId, setMatchId] = useState('');
  const [form, setForm] = useState({
    home_odds: '',
    draw_odds: '',
    away_odds: '',
    handicap: '',
  });
  const [busy, setBusy] = useState(false);
  const [loadingOdds, setLoadingOdds] = useState(false);

  async function selectMatch(id) {
    setMatchId(id);
    if (!id) {
      setForm({ home_odds: '', draw_odds: '', away_odds: '', handicap: '' });
      return;
    }
    setLoadingOdds(true);
    try {
      const o = await api.fixture(`/fixtures/${id}/odds`);
      setForm({
        home_odds: o.home_odds,
        draw_odds: o.draw_odds,
        away_odds: o.away_odds,
        handicap: o.handicap,
      });
    } catch {
      // No odds yet for this match — start from blank.
      setForm({ home_odds: '', draw_odds: '', away_odds: '', handicap: '' });
      toast.warn('Trận này chưa có kèo — nhập giá trị mới');
    } finally {
      setLoadingOdds(false);
    }
  }

  function setField(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function save() {
    const body = {
      home_odds: Number(form.home_odds),
      draw_odds: Number(form.draw_odds),
      away_odds: Number(form.away_odds),
      handicap: Number(form.handicap),
    };
    if (
      [body.home_odds, body.draw_odds, body.away_odds].some(
        (v) => !Number.isFinite(v) || v <= 1,
      ) ||
      !Number.isFinite(body.handicap)
    ) {
      toast.warn('Tỷ lệ 1X2 phải > 1 và handicap phải là số hợp lệ');
      return;
    }
    setBusy(true);
    try {
      await api.bff(`/admin/matches/${matchId}/odds`, { method: 'PUT', body });
      toast.success('Đã cập nhật kèo');
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  const matches = fixtures.data || [];

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>Quản lý kèo</h3>
      </div>
      <p className="hint">Chọn trận để xem và chỉnh tỷ lệ kèo (1X2 + handicap châu Á).</p>
      <label className="field" style={{ marginBottom: 14 }}>
        <span>Trận đấu</span>
        <select value={matchId} onChange={(e) => selectMatch(e.target.value)}>
          <option value="">— Chọn trận —</option>
          {matches.map((m) => (
            <option key={m.id} value={m.id}>
              {m.home_team} vs {m.away_team} · {formatDateTime(m.kickoff_at)}
            </option>
          ))}
        </select>
      </label>

      {matchId &&
        (loadingOdds ? (
          <div className="loading">Đang tải kèo…</div>
        ) : (
          <>
            <div className="inline-form">
              <label className="field">
                <span>Đội nhà (1X2)</span>
                <input
                  type="number"
                  step="0.01"
                  value={form.home_odds}
                  onChange={(e) => setField('home_odds', e.target.value)}
                />
              </label>
              <label className="field">
                <span>Hoà (1X2)</span>
                <input
                  type="number"
                  step="0.01"
                  value={form.draw_odds}
                  onChange={(e) => setField('draw_odds', e.target.value)}
                />
              </label>
              <label className="field">
                <span>Đội khách (1X2)</span>
                <input
                  type="number"
                  step="0.01"
                  value={form.away_odds}
                  onChange={(e) => setField('away_odds', e.target.value)}
                />
              </label>
              <label className="field">
                <span>Handicap (châu Á)</span>
                <input
                  type="number"
                  step="0.25"
                  value={form.handicap}
                  onChange={(e) => setField('handicap', e.target.value)}
                />
              </label>
            </div>
            <button
              className="btn btn-primary"
              style={{ marginTop: 14 }}
              onClick={save}
              disabled={busy}
            >
              {busy ? 'Đang lưu…' : 'Lưu kèo'}
            </button>
          </>
        ))}
    </div>
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

      <div className="section-title" style={{ marginTop: 28 }}>
        Kèo
      </div>
      <OddsManager />

      {pwUser && <PasswordModal user={pwUser} onClose={() => setPwUser(null)} />}
      {creating && (
        <CreateGroupModal onClose={() => setCreating(false)} onCreated={refreshGroups} />
      )}
    </div>
  );
}
