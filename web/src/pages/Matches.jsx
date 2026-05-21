import { useNavigate } from 'react-router-dom';
import { api } from '../api/client.js';
import { useFetch } from '../hooks/useFetch.js';
import { MatchCard } from '../components/MatchCard.jsx';

export function Matches() {
  const navigate = useNavigate();
  const { data, loading, error } = useFetch(() => api.fixture('/fixtures'), []);

  if (loading) return <div className="loading">Đang tải danh sách trận…</div>;
  if (error) return <div className="loading">Không tải được: {error.message}</div>;

  const matches = data || [];
  const upcoming = matches.filter((m) => m.status !== 'FINAL');
  const finished = matches.filter((m) => m.status === 'FINAL').reverse();

  return (
    <div>
      <div className="section-title">Sắp diễn ra ({upcoming.length})</div>
      {upcoming.length === 0 ? (
        <div className="loading">Không có trận sắp tới</div>
      ) : (
        <div className="grid">
          {upcoming.map((m) => (
            <MatchCard key={m.id} match={m} onClick={() => navigate(`/matches/${m.id}`)} />
          ))}
        </div>
      )}

      <div className="section-title">Đã kết thúc ({finished.length})</div>
      {finished.length === 0 ? (
        <div className="loading">Chưa có trận nào kết thúc</div>
      ) : (
        <div className="grid">
          {finished.map((m) => (
            <MatchCard key={m.id} match={m} onClick={() => navigate(`/matches/${m.id}`)} />
          ))}
        </div>
      )}
    </div>
  );
}
