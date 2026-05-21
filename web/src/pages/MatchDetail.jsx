import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { PieChart } from '../components/PieChart.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { Money } from '../components/Money.jsx';
import { formatDateTime } from '../utils/format.js';

export function MatchDetail() {
  const { matchId } = useParams();
  const [params] = useSearchParams();
  const { selectedGroupId } = useGroups();
  const groupId = params.get('group') || selectedGroupId;

  const { data, loading, error } = useFetch(
    () => api.bff(`/matches/${matchId}/detail?group_id=${groupId}`),
    [matchId, groupId],
  );

  if (!groupId) return <div className="loading">Chưa chọn group.</div>;
  if (loading) return <div className="loading">Đang tải chi tiết trận…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const isFinal = data.status === 'FINAL';
  const slices = [
    { label: data.home_team, value: data.pick_distribution.HOME, color: 'var(--brand)' },
    { label: 'Hoà', value: data.pick_distribution.DRAW, color: 'var(--gold)' },
    { label: data.away_team, value: data.pick_distribution.AWAY, color: 'var(--blue)' },
  ];

  const loserColumns = [
    { key: 'display_name', label: 'Người thua', render: (r) => <strong>{r.display_name}</strong> },
    {
      key: 'stake_minor',
      label: 'Tiền cược',
      align: 'right',
      render: (r) => <Money minor={r.stake_minor} tone="neg" />,
    },
  ];

  return (
    <div>
      <div className="panel">
        <div className="mc-teams" style={{ marginBottom: 4 }}>
          <div className="team">
            <div className="tname">{data.home_team}</div>
          </div>
          {isFinal ? (
            <div className="mc-score">
              {data.home_score} – {data.away_score}
            </div>
          ) : (
            <div className="mc-vs">VS</div>
          )}
          <div className="team">
            <div className="tname">{data.away_team}</div>
          </div>
        </div>
        <div className="hint" style={{ textAlign: 'center' }}>
          {formatDateTime(data.kickoff_at)} ·{' '}
          <span className={`badge ${data.status.toLowerCase()}`}>{data.status}</span>
        </div>
      </div>

      <div className="section-title">Phân bố lựa chọn trong group</div>
      <div className="panel">
        <PieChart slices={slices} />
      </div>

      <div className="section-title">
        Người thua trận này — tổng thu{' '}
        <Money minor={data.total_collected_minor} tone="auto" />
      </div>
      <DataTable
        columns={loserColumns}
        rows={data.losers}
        empty={isFinal ? 'Không ai thua trận này' : 'Trận chưa có kết quả'}
      />
    </div>
  );
}
