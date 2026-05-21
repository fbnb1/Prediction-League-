import { Countdown } from './Countdown.jsx';
import { formatDateTime } from '../utils/format.js';

const STATUS_LABEL = { SCHEDULED: 'Sắp đá', LOCKED: 'Đã khoá', FINAL: 'Kết thúc' };

// One match tile. Shows score when FINAL, otherwise a countdown to lock_at.
export function MatchCard({ match, onClick }) {
  const isFinal = match.status === 'FINAL';
  return (
    <div className={`card match-card ${onClick ? 'clickable' : ''}`} onClick={onClick}>
      <div className="mc-top">
        <span className="mc-round">{formatDateTime(match.kickoff_at)}</span>
        <span className={`badge ${match.status.toLowerCase()}`}>
          {STATUS_LABEL[match.status] || match.status}
        </span>
      </div>
      <div className="mc-teams">
        <div className="team">
          <div className="tname">{match.home_team}</div>
        </div>
        {isFinal ? (
          <div className="mc-score">
            {match.home_score} – {match.away_score}
          </div>
        ) : (
          <div className="mc-vs">VS</div>
        )}
        <div className="team">
          <div className="tname">{match.away_team}</div>
        </div>
      </div>
      <div className="mc-foot">
        {isFinal ? (
          <span className="mc-time">Tỷ số chung cuộc</span>
        ) : (
          <Countdown lockAt={match.lock_at} />
        )}
      </div>
    </div>
  );
}
