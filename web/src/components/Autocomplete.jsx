import { useMemo, useState } from 'react';

// Prefix-filtered picker. `options` is [{ value, label }].
export function Autocomplete({ options, value, onChange, placeholder }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);

  const selectedLabel = useMemo(
    () => options.find((o) => o.value === value)?.label || '',
    [options, value],
  );

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options.slice(0, 8);
    return options.filter((o) => o.label.toLowerCase().includes(q)).slice(0, 8);
  }, [options, query]);

  return (
    <div className="autocomplete">
      <input
        type="text"
        placeholder={placeholder}
        value={open ? query : selectedLabel}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => {
          setQuery('');
          setOpen(true);
        }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && matches.length > 0 && (
        <div className="autocomplete-list">
          {matches.map((o) => (
            <div
              key={o.value}
              className="autocomplete-item"
              onMouseDown={() => {
                onChange(o.value);
                setOpen(false);
              }}
            >
              {o.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
