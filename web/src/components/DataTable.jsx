import { useMemo, useState } from 'react';

// A sortable table. `columns` is
//   [{ key, label, sortable, render?(row), value?(row), align? }]
// `value` supplies the sort key when the cell isn't plain text.
export function DataTable({ columns, rows, onRowClick, empty = 'Không có dữ liệu' }) {
  const [sort, setSort] = useState({ key: null, dir: 1 });

  const sorted = useMemo(() => {
    if (!sort.key) return rows;
    const col = columns.find((c) => c.key === sort.key);
    const valueOf = col?.value || ((r) => r[sort.key]);
    return [...rows].sort((a, b) => {
      const va = valueOf(a);
      const vb = valueOf(b);
      if (va == null) return 1;
      if (vb == null) return -1;
      if (va < vb) return -sort.dir;
      if (va > vb) return sort.dir;
      return 0;
    });
  }, [rows, sort, columns]);

  function toggleSort(key) {
    setSort((s) => (s.key === key ? { key, dir: -s.dir } : { key, dir: 1 }));
  }

  if (rows.length === 0) {
    return <div className="table-wrap"><div className="loading">{empty}</div></div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={c.sortable ? 'sortable' : ''}
                style={{ textAlign: c.align || 'left' }}
                onClick={c.sortable ? () => toggleSort(c.key) : undefined}
              >
                {c.label}
                {sort.key === c.key && (
                  <span className="arrow"> {sort.dir === 1 ? '▲' : '▼'}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => (
            <tr
              key={row.id ?? row.user_id ?? row.match_id ?? i}
              className={onRowClick ? 'clickable' : ''}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((c) => (
                <td key={c.key} style={{ textAlign: c.align || 'left' }}>
                  {c.render ? c.render(row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
