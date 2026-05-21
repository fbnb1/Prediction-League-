const vnd = new Intl.NumberFormat('vi-VN');

// Money is stored in minor units (1/100). Display as whole đồng with the ₫ suffix.
export function formatMoney(amountMinor) {
  return `${vnd.format(Math.round((amountMinor || 0) / 100))} ₫`;
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}
