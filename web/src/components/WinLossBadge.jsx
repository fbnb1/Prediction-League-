// A settled-result pill. `result` is WON | LOST | PENDING.
const LABEL = { WON: 'Thắng', LOST: 'Thua', PENDING: 'Chờ' };

export function WinLossBadge({ result }) {
  const key = (result || 'PENDING').toLowerCase();
  return <span className={`badge ${key}`}>{LABEL[result] || result}</span>;
}
