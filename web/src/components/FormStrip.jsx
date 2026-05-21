// Five most-recent settled results, newest first. `form` is an array of "W"/"L".
export function FormStrip({ form = [] }) {
  const cells = [...form];
  while (cells.length < 5) cells.push(null);
  return (
    <span className="form-strip">
      {cells.slice(0, 5).map((r, i) => (
        <span
          key={i}
          className={`form-cell ${r === 'W' ? 'w' : r === 'L' ? 'l' : 'empty'}`}
        >
          {r || ''}
        </span>
      ))}
    </span>
  );
}
