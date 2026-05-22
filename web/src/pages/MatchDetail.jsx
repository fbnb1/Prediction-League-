import { useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api, ApiError } from '../api/client.js';
import { useGroups } from '../context/GroupContext.jsx';
import { useFetch } from '../hooks/useFetch.js';
import { PieChart } from '../components/PieChart.jsx';
import { DataTable } from '../components/DataTable.jsx';
import { Points } from '../components/Points.jsx';
import { useToast } from '../components/Toast.jsx';
import { formatDateTime } from '../utils/format.js';

function fmtOdds(v) {
  return typeof v === 'number' ? v.toFixed(2) : '—';
}

function fmtHandicap(h) {
  if (typeof h !== 'number') return '—';
  return h > 0 ? `+${h}` : `${h}`;
}

// One odds box. Renders as a <button> when `onPick` is supplied, otherwise a
// static read-only cell.
function OddsCell({ label, value, active, disabled, onPick }) {
  const content = (
    <>
      <span className="oc-label">{label}</span>
      <span className="oc-value">{fmtOdds(value)}</span>
    </>
  );
  if (!onPick) {
    return <div className={`odds-cell ${active ? 'active' : ''}`}>{content}</div>;
  }
  return (
    <button
      type="button"
      className={`odds-cell ${active ? 'active' : ''}`}
      disabled={disabled}
      onClick={onPick}
    >
      {content}
    </button>
  );
}

export function MatchDetail() {
  const { matchId } = useParams();
  const [params] = useSearchParams();
  const { selectedGroupId, selectedGroup } = useGroups();
  const groupId = params.get('group') || selectedGroupId;
  const toast = useToast();

  const detail = useFetch(
    () => api.bff(`/matches/${matchId}/detail?group_id=${groupId}`),
    [matchId, groupId],
    { refreshInterval: 60000 },
  );
  // Odds may not exist yet (404) -> handled softly via the error state.
  const odds = useFetch(
    () => api.fixture(`/fixtures/${matchId}/odds`),
    [matchId],
  );
  const myPicks = useFetch(() => api.prediction('/picks/mine'), []);

  const [submitting, setSubmitting] = useState(null); // outcome being submitted
  const [betError, setBetError] = useState(null);

  if (!groupId) return <div className="loading">Chưa chọn group.</div>;
  if (detail.loading) return <div className="loading">Đang tải chi tiết trận…</div>;
  if (detail.error)
    return <div className="loading">Không tải được: {detail.error.message}</div>;

  const data = detail.data;
  const isFinal = data.status === 'FINAL' || data.status === 'SETTLED';
  const canBet = data.status === 'SCHEDULED';
  const betType = selectedGroup?.bet_type || 'EUROPEAN';

  const o = odds.error ? null : odds.data;
  const myPick = (myPicks.data || []).find(
    (p) => p.match_id === matchId && p.group_id === groupId,
  );
  const picked = myPick?.predicted_outcome || null;

  async function submitPick(outcome) {
    setBetError(null);
    setSubmitting(outcome);
    try {
      await api.prediction('/picks', {
        method: 'POST',
        body: { group_id: groupId, match_id: matchId, predicted_outcome: outcome },
      });
      toast.success('Đã dự đoán');
      myPicks.reload();
      detail.reload();
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : 'Không đặt được dự đoán';
      setBetError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(null);
    }
  }

  const isAsian = betType === 'ASIAN';
  // The chart shows only locked picks (pick_distribution from the backend);
  // a pick becomes visible here once betting closes and it locks.
  const dist = data.pick_distribution;
  const slices = isAsian
    ? [
        { label: data.home_team, value: dist.HOME, color: 'var(--brand)' },
        { label: data.away_team, value: dist.AWAY, color: 'var(--blue)' },
      ]
    : [
        { label: data.home_team, value: dist.HOME, color: 'var(--brand)' },
        { label: 'Hoà', value: dist.DRAW, color: 'var(--gold)' },
        { label: data.away_team, value: dist.AWAY, color: 'var(--blue)' },
      ];

  const loserColumns = [
    { key: 'display_name', label: 'Người thua', render: (r) => <strong>{r.display_name}</strong> },
    {
      key: 'round_multiplier',
      label: 'Điểm thua',
      align: 'right',
      render: (r) => <Points pts={r.round_multiplier} tone="neg" />,
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

      <div className="section-title">Dự đoán</div>
      {odds.loading ? (
        <div className="panel">
          <div className="hint" style={{ margin: 0 }}>Đang tải tỷ lệ kèo…</div>
        </div>
      ) : !o ? (
        <div className="panel">
          <div className="hint" style={{ margin: 0 }}>Trận này chưa có tỷ lệ kèo.</div>
        </div>
      ) : (
        <>
          {isAsian ? (
            /* Kèo châu Á (Handicap) — group dùng kèo châu Á */
            <div className="panel">
              <div className="panel-head">
                <h3>
                  Dự đoán (Châu Á){' '}
                  <span className="badge asian" style={{ marginLeft: 6 }}>
                    Đang áp dụng
                  </span>
                </h3>
              </div>
              <div className="odds-line">
                Đường handicap (đội nhà):{' '}
                <strong>{fmtHandicap(o.handicap)}</strong>
              </div>
              <div className="odds-grid cols-2">
                <OddsCell
                  label={data.home_team}
                  value={o.home_odds}
                  active={picked === 'HOME'}
                  disabled={submitting !== null}
                  onPick={canBet ? () => submitPick('HOME') : undefined}
                />
                <OddsCell
                  label={data.away_team}
                  value={o.away_odds}
                  active={picked === 'AWAY'}
                  disabled={submitting !== null}
                  onPick={canBet ? () => submitPick('AWAY') : undefined}
                />
              </div>
            </div>
          ) : (
            /* Kèo châu Âu (1X2) — group dùng kèo châu Âu */
            <div className="panel">
              <div className="panel-head">
                <h3>
                  Dự đoán (Châu Âu){' '}
                  <span className="badge european" style={{ marginLeft: 6 }}>
                    Đang áp dụng
                  </span>
                </h3>
              </div>
              <div className="odds-grid cols-3">
                <OddsCell
                  label={data.home_team}
                  value={o.home_odds}
                  active={picked === 'HOME'}
                  disabled={submitting !== null}
                  onPick={canBet ? () => submitPick('HOME') : undefined}
                />
                <OddsCell
                  label="Hoà"
                  value={o.draw_odds}
                  active={picked === 'DRAW'}
                  disabled={submitting !== null}
                  onPick={canBet ? () => submitPick('DRAW') : undefined}
                />
                <OddsCell
                  label={data.away_team}
                  value={o.away_odds}
                  active={picked === 'AWAY'}
                  disabled={submitting !== null}
                  onPick={canBet ? () => submitPick('AWAY') : undefined}
                />
              </div>
            </div>
          )}

          {!canBet ? (
            <div className="hint">Đã khoá dự đoán cho trận này.</div>
          ) : picked ? (
            <div className="bet-status ok">
              Bạn đang đặt: <strong>
                {picked === 'HOME'
                  ? data.home_team
                  : picked === 'AWAY'
                    ? data.away_team
                    : 'Hoà'}
              </strong>{' '}
              · bấm ô khác để đổi.
            </div>
          ) : (
            <div className="hint">
              Chọn kết quả để dự đoán.
            </div>
          )}
          {betError && <div className="bet-status err">{betError}</div>}
        </>
      )}

      <div className="section-title">Phân bố lựa chọn trong group</div>
      <div className="panel">
        <PieChart slices={slices} />
      </div>

      <div className="section-title">
        Người thua trận này — tổng điểm{' '}
        <Points pts={data.total_points} tone="neg" />
      </div>
      <DataTable
        columns={loserColumns}
        rows={data.losers}
        empty={isFinal ? 'Không ai thua trận này' : 'Trận chưa có kết quả'}
      />
    </div>
  );
}
