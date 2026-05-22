import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { PieChart } from '../components/PieChart.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { WinLossBadge } from '../components/WinLossBadge.jsx';
import { Points } from '../components/Points.jsx';
import { formatDateTime } from '../utils/format.js';

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
    { label: 'Đúng', value: wins, color: 'var(--brand)' },
    { label: 'Sai', value: losses, color: 'var(--red)' },
  ];

  const pickColumns = [
    {
      key: 'match',
      label: 'Trận',
      render: (p) => <strong>{p.home_team} – {p.away_team}</strong>,
    },
    { key: 'kickoff_at', label: 'Thời điểm', render: (p) => formatDateTime(p.kickoff_at) },
    { key: 'predicted_outcome', label: 'Dự đoán', render: (p) => p.predicted_outcome || '—' },
    {
      key: 'round_multiplier',
      label: 'Hệ số',
      align: 'right',
      render: (p) => `×${p.round_multiplier}`,
    },
    { key: 'result', label: 'Kết quả', render: (p) => <WinLossBadge result={p.result} /> },
  ];

  return (
    <div>
      <div className="section-title">{data.display_name}</div>

      <div className="stat-cards">
        <div className="stat-card">
          <div className="sc-label">Điểm thua</div>
          <div className="sc-value">
            <Points pts={data.points_lost} tone="neg" />
          </div>
        </div>
      </div>

      <div className="section-title">Tỷ lệ đúng / sai</div>
      <div className="panel">
        <PieChart slices={slices} />
      </div>

      <div className="section-title">Lịch sử dự đoán ({data.picks.length})</div>
      <DataTable columns={pickColumns} rows={data.picks} empty="Chưa có dự đoán nào" />
    </div>
  );
}
