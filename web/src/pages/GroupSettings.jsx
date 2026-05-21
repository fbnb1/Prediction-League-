import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { Autocomplete } from '../components/Autocomplete.jsx';
import { Money } from '../components/Money.jsx';
import { useToast } from '../components/Toast.jsx';
import { formatDateTime } from '../utils/format.js';

function BetTypePanel({ groupId, group, onChanged }) {
  const toast = useToast();
  const [betType, setBetType] = useState(group?.bet_type || 'EUROPEAN');
  const [busy, setBusy] = useState(false);

  async function save() {
    setBusy(true);
    try {
      await api.prediction(`/admin/groups/${groupId}/bet-type`, {
        method: 'PUT',
        body: { bet_type: betType },
      });
      toast.success('Đã cập nhật loại kèo');
      onChanged();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>Loại kèo</h3>
      </div>
      <div className="inline-form">
        <select value={betType} onChange={(e) => setBetType(e.target.value)}>
          <option value="EUROPEAN">Châu Âu (1X2)</option>
          <option value="ASIAN">Châu Á (handicap)</option>
        </select>
        <button
          className="btn btn-primary"
          onClick={save}
          disabled={busy || betType === group?.bet_type}
        >
          Lưu
        </button>
      </div>
    </div>
  );
}

function MembersPanel({ groupId }) {
  const toast = useToast();
  const members = useFetch(
    () => api.prediction(`/groups/${groupId}/members`),
    [groupId],
  );
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

  const columns = [
    { key: 'display_name', label: 'Thành viên', render: (m) => <strong>{m.display_name}</strong> },
    { key: 'username', label: 'Đăng nhập', render: (m) => <span className="mono">{m.username}</span> },
  ];

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>Thành viên</h3>
      </div>
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
      {members.loading ? (
        <div className="loading">Đang tải thành viên…</div>
      ) : (
        <DataTable columns={columns} rows={members.data} empty="Group chưa có thành viên" />
      )}
    </div>
  );
}

function DepositsPanel({ groupId }) {
  const toast = useToast();
  const members = useFetch(
    () => api.prediction(`/groups/${groupId}/members`),
    [groupId],
  );
  const deposits = useFetch(() => api.bff(`/groups/${groupId}/deposits`), [groupId]);
  const [depositor, setDepositor] = useState('');
  const [amount, setAmount] = useState('');
  const [busy, setBusy] = useState(false);

  const memberOptions = (members.data || []).map((m) => ({
    value: m.user_id,
    label: `${m.display_name} (${m.username})`,
  }));

  async function submit() {
    const dong = Number(amount);
    if (!depositor || !Number.isFinite(dong) || dong <= 0) {
      toast.warn('Chọn thành viên và nhập số tiền hợp lệ');
      return;
    }
    setBusy(true);
    try {
      await api.bff(`/admin/groups/${groupId}/deposits`, {
        method: 'POST',
        body: { depositor, amount_minor: Math.round(dong * 100) },
      });
      toast.success('Đã ghi nhận khoản nạp');
      setAmount('');
      setDepositor('');
      deposits.reload();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setBusy(false);
    }
  }

  const columns = [
    { key: 'display_name', label: 'Người nạp', render: (d) => <strong>{d.display_name}</strong> },
    {
      key: 'amount_minor',
      label: 'Số tiền',
      align: 'right',
      render: (d) => <Money minor={d.amount_minor} tone="auto" />,
    },
    { key: 'posted_at', label: 'Thời điểm', render: (d) => formatDateTime(d.posted_at) },
  ];

  return (
    <div className="panel">
      <div className="panel-head">
        <h3>Nạp tiền</h3>
      </div>
      <div className="inline-form" style={{ marginBottom: 14 }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <Autocomplete
            options={memberOptions}
            value={depositor}
            onChange={setDepositor}
            placeholder="Chọn thành viên…"
          />
        </div>
        <input
          type="number"
          min="1"
          placeholder="Số tiền (₫)"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          style={{ flex: 1, minWidth: 140 }}
        />
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          Ghi nhận
        </button>
      </div>
      {deposits.loading ? (
        <div className="loading">Đang tải lịch sử nạp…</div>
      ) : (
        <DataTable columns={columns} rows={deposits.data} empty="Chưa có khoản nạp nào" />
      )}
    </div>
  );
}

export function GroupSettings() {
  const { groupId } = useParams();
  const { groups, refresh } = useGroups();
  const group = groups.find((g) => g.id === groupId);

  return (
    <div>
      <div className="section-title">{group ? group.name : groupId}</div>
      <BetTypePanel groupId={groupId} group={group} onChanged={refresh} />
      <MembersPanel groupId={groupId} />
      <DepositsPanel groupId={groupId} />
    </div>
  );
}
