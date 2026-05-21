import { formatMoney } from '../utils/format.js';

// Renders a minor-unit amount. `tone` controls colour:
//   'auto'  -> green positive / red negative
//   'neg'   -> always red (e.g. money lost / owed)
//   'plain' -> neutral
export function Money({ minor = 0, tone = 'plain' }) {
  let cls = 'zero';
  if (tone === 'neg') {
    cls = minor > 0 ? 'neg' : 'zero';
  } else if (tone === 'auto') {
    cls = minor > 0 ? 'pos' : minor < 0 ? 'neg' : 'zero';
  }
  return <span className={`money ${cls}`}>{formatMoney(minor)}</span>;
}
