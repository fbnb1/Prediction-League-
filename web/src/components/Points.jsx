// Points: renders an integer point count.
// tone: 'neg' -> red when pts > 0;  'plain' -> always neutral
export function Points({ pts = 0, tone = 'plain' }) {
  let cls = 'zero';
  if (tone === 'neg' && pts > 0) cls = 'neg';
  return <span className={`money ${cls}`}>{pts} điểm</span>;
}
