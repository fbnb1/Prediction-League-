import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { DataTable } from '../components/DataTable.jsx';
import { FormStrip } from '../components/FormStrip.jsx';
import { MatchCard } from '../components/MatchCard.jsx';
import { Money } from '../components/Money.jsx';
import { formatDateTime } from '../utils/format.js';

function LeaderboardTable({ groupId }) {
  const navigate = useNavigate();
  const { data, loading, error } = useFetch(
    () => api.bff(`/groups/${groupId}/leaderboard`),
    [groupId],
  );

  if (loading) return <div className="loading">Đang tải bảng xếp hạng…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const columns = [
    {
      key: 'display_name',
      label: 'Người chơi',
      sortable: true,
      render: (r) => <strong>{r.display_name}</strong>,
    },
    {
      key: 'money_lost_minor',
      label: 'Đã thua',
      sortable: true,
      align: 'right',
      render: (r) => <Money minor={r.money_lost_minor} tone="neg" />,
    },
    {
      key: 'money_owed_minor',
      label: 'Còn nợ',
      sortable: true,
      align: 'right',
      render: (r) => <Money minor={r.money_owed_minor} tone="neg" />,
    },
    {
      key: 'win_rate',
      label: 'Tỷ lệ thắng',
      sortable: true,
      align: 'right',
      render: (r) => `${Math.round(r.win_rate * 100)}%`,
    },
    {
      key: 'form',
      label: 'Phong độ',
      render: (r) => <FormStrip form={r.form} />,
    },
  ];

  return (
    <DataTable
      columns={columns}
      rows={data}
      onRowClick={(r) => navigate(`/players/${r.user_id}?group=${groupId}`)}
      empty="Group chưa có thành viên nào"
    />
  );
}

function MatchesStrip() {
  const navigate = useNavigate();
  const { data, loading } = useFetch(() => api.fixture('/fixtures'), []);

  if (loading) return <div className="loading">Đang tải trận đấu…</div>;
  const matches = data || [];
  const finals = matches
    .filter((m) => m.status === 'FINAL')
    .slice(-3)
    .reverse();
  const upcoming = matches.filter((m) => m.status !== 'FINAL').slice(0, 3);
  const shown = [...upcoming, ...finals];

  if (shown.length === 0) {
    return <div className="loading">Chưa có trận nào</div>;
  }
  return (
    <div className="grid">
      {shown.map((m) => (
        <MatchCard
          key={m.id}
          match={m}
          onClick={() => navigate(`/matches/${m.id}`)}
        />
      ))}
    </div>
  );
}

function DepositsTable({ groupId }) {
  const { data, loading } = useFetch(
    () => api.bff(`/groups/${groupId}/deposits`),
    [groupId],
  );
  if (loading) return <div className="loading">Đang tải lịch sử nạp…</div>;

  const columns = [
    { key: 'display_name', label: 'Người nạp', render: (r) => <strong>{r.display_name}</strong> },
    {
      key: 'amount_minor',
      label: 'Số tiền',
      align: 'right',
      render: (r) => <Money minor={r.amount_minor} tone="auto" />,
    },
    { key: 'posted_at', label: 'Thời điểm', render: (r) => formatDateTime(r.posted_at) },
  ];
  return <DataTable columns={columns} rows={data || []} empty="Chưa có khoản nạp nào" />;
}

export function Home() {
  const { selectedGroupId, selectedGroup, loading } = useGroups();

  if (loading) return <div className="loading">Đang tải group…</div>;
  if (!selectedGroupId) {
    return (
      <div className="empty">
        <span className="ee">📭</span>
        <p>Bạn chưa thuộc group nào. Liên hệ quản trị viên để được thêm vào.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="section-title">
        Bảng xếp hạng — {selectedGroup?.name}
      </div>
      <LeaderboardTable groupId={selectedGroupId} />

      <div className="section-title">Trận đấu</div>
      <MatchesStrip />

      <div className="section-title">Lịch sử nạp tiền của group</div>
      <DepositsTable groupId={selectedGroupId} />
    </div>
  );
}
