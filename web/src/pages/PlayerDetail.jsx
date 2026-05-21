import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { PieChart } from '../components/PieChart.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { WinLossBadge } from '../components/WinLossBadge.jsx';
import { Money } from '../components/Money.jsx';
import { formatDateTime } from '../utils/format.js';

function StatCard({ label, minor, tone }) {
  return (
    <div className="stat-card">
      <div className="sc-label">{label}</div>
      <div className="sc-value">
        <Money minor={minor} tone={tone} />
      </div>
    </div>
  );
}

export function PlayerDetail() {
  const { userId } = useParams();
  const [params] = useSearchParams();
  const { selectedGroupId } = useGroups();
  const groupId = params.get('group') || selectedGroupId;

  const { data, loading, error } = useFetch(
    () => api.bff(`/groups/${groupId}/members/${userId}/summary`),
    [groupId, userId],
  );

  if (!groupId) return <div className="loading">Chưa chọn group.</div>;
  if (loading) return <div className="loading">Đang tải chi tiết người chơi…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const wins = data.picks.filter((p) => p.result === 'WON').length;
  const losses = data.picks.filter((p) => p.result === 'LOST').length;
  const slices = [
    { label: 'Thắng', value: wins, color: 'var(--brand)' },
    { label: 'Thua', value: losses, color: 'var(--red)' },
  ];

  const pickColumns = [
    {
      key: 'match',
      label: 'Trận',
      render: (p) => (
        <strong>
          {p.home_team} – {p.away_team}
        </strong>
      ),
    },
    { key: 'kickoff_at', label: 'Thời điểm', render: (p) => formatDateTime(p.kickoff_at) },
    { key: 'predicted_outcome', label: 'Dự đoán', render: (p) => p.predicted_outcome || '—' },
    {
      key: 'stake_minor',
      label: 'Tiền cược',
      align: 'right',
      render: (p) => <Money minor={p.stake_minor} tone="plain" />,
    },
    { key: 'result', label: 'Kết quả', render: (p) => <WinLossBadge result={p.result} /> },
  ];

  const depositColumns = [
    {
      key: 'amount_minor',
      label: 'Số tiền',
      align: 'right',
      render: (d) => <Money minor={d.amount_minor} tone="auto" />,
    },
    { key: 'posted_at', label: 'Thời điểm', render: (d) => formatDateTime(d.posted_at) },
  ];

  return (
    <div>
      <div className="section-title">{data.display_name}</div>

      <div className="stat-cards">
        <StatCard label="Đã thua" minor={data.money_lost_minor} tone="neg" />
        <StatCard label="Đã nộp" minor={data.money_deposited_minor} tone="auto" />
        <StatCard label="Còn phải đóng" minor={data.money_owed_minor} tone="neg" />
      </div>

      <div className="section-title">Tỷ lệ thắng / thua</div>
      <div className="panel">
        <PieChart slices={slices} />
      </div>

      <div className="section-title">Lịch sử dự đoán ({data.picks.length})</div>
      <DataTable columns={pickColumns} rows={data.picks} empty="Chưa có dự đoán nào" />

      <div className="section-title">Lịch sử nạp tiền</div>
      <DataTable
        columns={depositColumns}
        rows={data.deposits}
        empty="Chưa có khoản nạp nào"
      />
    </div>
  );
}
