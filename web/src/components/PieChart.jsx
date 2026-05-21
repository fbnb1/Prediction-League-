// Hand-drawn SVG pie chart -- no chart library. `slices` is
// [{ label, value, color }]. Zero-total renders an empty ring.
const SIZE = 132;
const R = 60;
const CENTER = SIZE / 2;

function arcPath(startAngle, endAngle) {
  const start = polar(startAngle);
  const end = polar(endAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${CENTER} ${CENTER} L ${start.x} ${start.y} A ${R} ${R} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
}

function polar(angleDeg) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return { x: CENTER + R * Math.cos(rad), y: CENTER + R * Math.sin(rad) };
}

export function PieChart({ slices }) {
  const total = slices.reduce((sum, s) => sum + s.value, 0);

  return (
    <div className="pie-wrap">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`}>
        {total === 0 ? (
          <circle
            cx={CENTER}
            cy={CENTER}
            r={R}
            fill="none"
            stroke="var(--line)"
            strokeWidth="2"
          />
        ) : (
          (() => {
            let angle = 0;
            return slices
              .filter((s) => s.value > 0)
              .map((s) => {
                const sweep = (s.value / total) * 360;
                const path = arcPath(angle, angle + sweep);
                angle += sweep;
                return <path key={s.label} d={path} fill={s.color} />;
              });
          })()
        )}
      </svg>
      <div className="pie-legend">
        {slices.map((s) => (
          <div key={s.label} className="pl-row">
            <span className="pl-dot" style={{ background: s.color }} />
            <span>
              {s.label}: <strong>{s.value}</strong>
              {total > 0 && (
                <span style={{ color: 'var(--text-mute)' }}>
                  {' '}
                  ({Math.round((s.value / total) * 100)}%)
                </span>
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
