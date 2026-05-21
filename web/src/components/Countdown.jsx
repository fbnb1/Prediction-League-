import { useEffect, useState } from 'react';

function diffParts(target) {
  const ms = new Date(target).getTime() - Date.now();
  return { ms, abs: Math.abs(ms) };
}

function label(abs) {
  const totalMin = Math.floor(abs / 60000);
  const days = Math.floor(totalMin / 1440);
  const hours = Math.floor((totalMin % 1440) / 60);
  const mins = totalMin % 60;
  const secs = Math.floor((abs % 60000) / 1000);
  if (days > 0) return `${days}n ${hours}g`;
  if (hours > 0) return `${hours}g ${String(mins).padStart(2, '0')}p`;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

// Counts down to `lockAt`; once passed, shows how long ago picks locked.
export function Countdown({ lockAt }) {
  const [, tick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => tick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, []);

  if (!lockAt) return <span className="countdown passed">—</span>;
  const { ms, abs } = diffParts(lockAt);
  if (ms <= 0) return <span className="countdown passed">Đã khoá {label(abs)} trước</span>;
  return (
    <span className={`countdown ${abs < 600000 ? 'live' : ''}`}>
      Khoá sau {label(abs)}
    </span>
  );
}
