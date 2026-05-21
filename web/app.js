/* ============================================================
   Prediction League — single-page web UI
   Talks to the gateway at /api/{prediction,fixture,ledger}.
   ============================================================ */

const API = {
  prediction: '/api/prediction',
  fixture: '/api/fixture',
  ledger: '/api/ledger',
};

// Shared pool every user is auto-enrolled into (see prediction-service config).
const DEFAULT_POOL_ID = 'grp-default-pool';
const sortGroups = (gs) => [...gs].sort((a, b) =>
  (a.id === DEFAULT_POOL_ID ? -1 : 0) - (b.id === DEFAULT_POOL_ID ? -1 : 0));

const store = {
  get token()    { return localStorage.getItem('pl_token'); },
  set token(v)   { v ? localStorage.setItem('pl_token', v) : localStorage.removeItem('pl_token'); },
  get user()     { try { return JSON.parse(localStorage.getItem('pl_user')); } catch { return null; } },
  set user(v)    { v ? localStorage.setItem('pl_user', JSON.stringify(v)) : localStorage.removeItem('pl_user'); },
  get adminKey() { return localStorage.getItem('pl_admin_key') || 'dev-admin-key-change-me'; },
  set adminKey(v){ localStorage.setItem('pl_admin_key', v); },
};

/* ---------- HTTP helper ---------- */
async function api(path, { method = 'GET', body, auth = false, adminKey = false } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && store.token) headers['Authorization'] = `Bearer ${store.token}`;
  if (adminKey) headers['X-Admin-Api-Key'] = store.adminKey;

  let res;
  try {
    res = await fetch(path, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch (e) {
    throw new ApiError('Network error', 'Could not reach the service.');
  }

  const text = await res.text();
  let data = null;
  if (text) { try { data = JSON.parse(text); } catch { data = text; } }

  if (!res.ok) {
    const detail = (data && (data.detail || data.message || data.error)) || `HTTP ${res.status}`;
    throw new ApiError(`Request failed (${res.status})`, String(detail));
  }
  return data;
}
class ApiError extends Error {
  constructor(title, detail) { super(detail); this.title = title; this.detail = detail; }
}

/* ---------- Toasts ---------- */
function toast(title, detail = '', kind = '') {
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.innerHTML = `<strong>${esc(title)}</strong>${detail ? `<small>${esc(detail)}</small>` : ''}`;
  document.getElementById('toasts').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; el.style.transform = 'translateX(30px)'; el.style.transition = 'all .3s'; }, 3600);
  setTimeout(() => el.remove(), 3950);
}
function toastErr(e) {
  if (e instanceof ApiError) toast(e.title, e.detail, 'error');
  else toast('Something went wrong', e.message || '', 'error');
}

/* ---------- Small utils ---------- */
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;' }[c]));
const $  = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

function money(minor) {
  const v = (minor || 0) / 100;
  return v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
}
function relTime(iso) {
  if (!iso) return '';
  const diff = new Date(iso) - Date.now();
  const abs = Math.abs(diff);
  const mins = Math.round(abs / 60000);
  if (mins < 60) return diff > 0 ? `in ${mins}m` : `${mins}m ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 48) return diff > 0 ? `in ${hrs}h` : `${hrs}h ago`;
  const days = Math.round(hrs / 24);
  return diff > 0 ? `in ${days}d` : `${days}d ago`;
}
const FLAGS = {
  Argentina:'🇦🇷',Brazil:'🇧🇷',France:'🇫🇷',England:'🏴󠁧󠁢󠁥󠁮󠁧󠁿',Spain:'🇪🇸',Germany:'🇩🇪',
  Portugal:'🇵🇹',Netherlands:'🇳🇱',Belgium:'🇧🇪',Croatia:'🇭🇷',Italy:'🇮🇹',Uruguay:'🇺🇾',
  Mexico:'🇲🇽',USA:'🇺🇸','United States':'🇺🇸',Canada:'🇨🇦',Japan:'🇯🇵',Morocco:'🇲🇦',
  Senegal:'🇸🇳',Switzerland:'🇨🇭',Denmark:'🇩🇰',Poland:'🇵🇱',Korea:'🇰🇷','South Korea':'🇰🇷',
};
const flag = (t) => FLAGS[t] || '⚽';
const outcomeLabel = (o) => ({ HOME:'Home win', DRAW:'Draw', AWAY:'Away win' }[o] || o || '—');

// Asian-handicap label for the HOME team: positive = home gives the line.
function ahLabel(h) {
  h = Number(h) || 0;
  if (h === 0) return 'level (0)';
  const v = Math.abs(h).toFixed(1);
  return h > 0 ? `-${v}` : `+${v}`;
}

/* ============================================================
   AUTH
   ============================================================ */
$$('[data-authtab]').forEach(btn => btn.addEventListener('click', () => {
  $$('[data-authtab]').forEach(b => b.classList.toggle('active', b === btn));
  const t = btn.dataset.authtab;
  $('#login-form').classList.toggle('hidden', t !== 'login');
  $('#register-form').classList.toggle('hidden', t !== 'register');
}));

$('#login-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target;
  try {
    const data = await api(`${API.prediction}/auth/login`, {
      method: 'POST',
      body: { username: f.username.value.trim(), password: f.password.value },
    });
    onAuthed(data);
  } catch (err) { toastErr(err); }
});

$('#register-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const f = e.target;
  try {
    const data = await api(`${API.prediction}/auth/register`, {
      method: 'POST',
      body: { username: f.username.value.trim(), password: f.password.value },
    });
    toast('Welcome aboard', 'Your account is ready.');
    onAuthed(data);
  } catch (err) { toastErr(err); }
});

function onAuthed(data) {
  store.token = data.access_token;
  store.user = { id: data.user_id, name: data.display_name };
  enterApp();
}

$('#logout-btn').addEventListener('click', () => {
  store.token = null;
  store.user = null;
  location.reload();
});

/* ============================================================
   APP SHELL
   ============================================================ */
const VIEW_META = {
  matches: { title: 'Matches', sub: 'Upcoming World Cup fixtures and live odds.' },
  groups:  { title: 'My Groups', sub: 'Create or join prediction pools with friends.' },
  picks:   { title: 'My Picks', sub: 'Every prediction you have placed.' },
  ledger:  { title: 'Ledger', sub: 'Double-entry accounts, journal entries and audit trail.' },
  admin:   { title: 'Admin Console', sub: 'Operate the settlement saga end to end.' },
};

let currentView = 'matches';

function enterApp() {
  const u = store.user;
  $('#auth-screen').classList.add('hidden');
  $('#app').classList.remove('hidden');
  $('#user-name').textContent = u?.name || 'User';
  $('#user-id').textContent = (u?.id || '').slice(0, 16);
  $('#user-avatar').textContent = (u?.name || 'U').trim().charAt(0).toUpperCase();
  $('#admin-key').value = store.adminKey;
  switchView('matches');
  checkServices();
}

$$('.nav-item').forEach(btn => btn.addEventListener('click', () => switchView(btn.dataset.view)));

function switchView(view) {
  currentView = view;
  $$('.nav-item').forEach(b => b.classList.toggle('active', b.dataset.view === view));
  $$('.view').forEach(v => v.classList.add('hidden'));
  $(`#view-${view}`).classList.remove('hidden');
  $('#view-title').textContent = VIEW_META[view].title;
  $('#view-sub').textContent = VIEW_META[view].sub;
  loadView(view);
}

$('#refresh-btn').addEventListener('click', () => { loadView(currentView); checkServices(); });

function loadView(view) {
  ({
    matches: loadMatches,
    groups:  loadGroups,
    picks:   loadPicks,
    ledger:  loadLedger,
    admin:   loadAdmin,
  }[view] || (() => {}))();
}

/* ---------- Service status ---------- */
async function checkServices() {
  const box = $('#service-status');
  const svcs = [
    { name: 'Prediction', url: `${API.prediction}/health` },
    { name: 'Fixture',    url: `${API.fixture}/health` },
    { name: 'Ledger',     url: `${API.ledger}/actuator/health` },
  ];
  box.innerHTML = svcs.map(s => `<div class="svc" data-svc="${s.name}"><span class="dot"></span>${s.name}</div>`).join('');
  svcs.forEach(async (s) => {
    const el = box.querySelector(`[data-svc="${s.name}"]`);
    try {
      const r = await fetch(s.url);
      el.classList.add(r.ok ? 'up' : 'down');
    } catch { el.classList.add('down'); }
  });
}

/* ============================================================
   MATCHES
   ============================================================ */
let matchCache = [];
let oddsCache = {};

async function loadMatches() {
  const grid = $('#matches-grid');
  grid.innerHTML = skeletons(6);
  try {
    const matches = await api(`${API.fixture}/fixtures`);
    matchCache = matches;
    // odds, fetched in parallel; tolerate misses
    await Promise.all(matches.map(async (m) => {
      try { oddsCache[m.id] = await api(`${API.fixture}/fixtures/${m.id}/odds`); }
      catch { /* odds optional */ }
    }));
    renderMatches(matches);
  } catch (err) {
    grid.innerHTML = emptyState('⚠️', 'Could not load fixtures', err.detail || '');
  }
}

function renderMatches(matches) {
  const grid = $('#matches-grid');
  if (!matches.length) { grid.innerHTML = emptyState('🏟️', 'No fixtures yet', 'Run a sync from the Admin Console.'); return; }
  grid.innerHTML = matches.map(matchCardHTML).join('');
  grid.querySelectorAll('[data-pick]').forEach(btn =>
    btn.addEventListener('click', () => openPickModal(btn.dataset.pick)));
}

function matchCardHTML(m) {
  const o = oddsCache[m.id];
  const status = (m.status || 'scheduled').toLowerCase();
  const settled = status === 'settled';
  const canPick = status === 'scheduled';
  const scoreOrVs = settled
    ? `<div class="mc-score">${m.home_score ?? 0} – ${m.away_score ?? 0}</div>`
    : `<div class="mc-vs">VS</div>`;
  const oddsBlock = o ? `
    <div class="mc-odds">
      <div class="odd"><div class="ol">HOME</div><div class="ov">${o.home_odds.toFixed(2)}</div></div>
      <div class="odd"><div class="ol">DRAW</div><div class="ov">${o.draw_odds.toFixed(2)}</div></div>
      <div class="odd"><div class="ol">AWAY</div><div class="ov">${o.away_odds.toFixed(2)}</div></div>
    </div>` : '';
  const hcap = o ? Number(o.handicap) : 0;
  const ahBlock = o ? `
    <div class="ah-line">⚖️ Asian line — ${esc(m.home_team)} ${ahLabel(hcap)}</div>` : '';
  return `
  <div class="card match-card">
    <div class="mc-top">
      <span class="mc-round">${esc(m.group_code ? 'Group ' + m.group_code : 'Round ' + m.round_id)}</span>
      <span class="badge ${status}">${esc(status)}</span>
    </div>
    <div class="mc-teams">
      <div class="team"><div class="flag">${flag(m.home_team)}</div><div class="tname">${esc(m.home_team)}</div></div>
      ${scoreOrVs}
      <div class="team"><div class="flag">${flag(m.away_team)}</div><div class="tname">${esc(m.away_team)}</div></div>
    </div>
    ${oddsBlock}
    ${ahBlock}
    <div class="mc-foot">
      <span class="mc-time">🕑 ${fmtDate(m.kickoff_at)} · ${relTime(m.kickoff_at)}</span>
      ${canPick
        ? `<button class="btn btn-primary" data-pick="${esc(m.id)}">Predict</button>`
        : `<span class="badge ${settled ? 'settled' : 'locked'}">${settled ? 'Final' : 'Closed'}</span>`}
    </div>
  </div>`;
}

/* ---------- Pick modal ---------- */
let pickState = { matchId: null, outcome: null };
let pickGroups = [];

async function openPickModal(matchId) {
  const m = matchCache.find(x => x.id === matchId);
  if (!m) return;
  pickState = { matchId, outcome: null };
  $('#pick-modal-match').innerHTML =
    `${flag(m.home_team)} ${esc(m.home_team)} <span style="color:var(--text-mute)">vs</span> ${esc(m.away_team)} ${flag(m.away_team)}`;
  $('#outcome-picker').innerHTML = '';

  const sel = $('#pick-group');
  sel.innerHTML = '<option value="">Loading groups…</option>';
  $('#pick-modal').classList.remove('hidden');
  try {
    pickGroups = sortGroups(await api(`${API.prediction}/groups/mine`, { auth: true }));
    if (!pickGroups.length) {
      sel.innerHTML = '<option value="">No groups available</option>';
    } else {
      sel.innerHTML = pickGroups.map(g => {
        const mkt = g.bet_type === 'ASIAN' ? 'Asian handicap' : '1X2';
        return `<option value="${esc(g.id)}">${esc(g.name)} · ${mkt}</option>`;
      }).join('');
      renderOutcomePicker();
    }
  } catch (err) {
    sel.innerHTML = '<option value="">Could not load groups</option>';
    toastErr(err);
  }
}

// The outcome buttons depend on the selected group's betting market.
function renderOutcomePicker() {
  pickState.outcome = null;
  const box = $('#outcome-picker');
  const group = pickGroups.find(g => g.id === $('#pick-group').value);
  const m = matchCache.find(x => x.id === pickState.matchId);
  if (!group || !m) { box.innerHTML = ''; return; }

  let buttons;
  if (group.bet_type === 'ASIAN') {
    const h = oddsCache[m.id] ? Number(oddsCache[m.id].handicap) : 0;
    buttons = [
      { o: 'HOME', label: m.home_team, sub: `Handicap ${ahLabel(h)}` },
      { o: 'AWAY', label: m.away_team, sub: `Handicap ${ahLabel(-h)}` },
    ];
  } else {
    buttons = [
      { o: 'HOME', label: 'Home win', sub: m.home_team },
      { o: 'DRAW', label: 'Draw', sub: '' },
      { o: 'AWAY', label: 'Away win', sub: m.away_team },
    ];
  }
  box.innerHTML = buttons.map(b =>
    `<button class="outcome" data-outcome="${b.o}">${esc(b.label)}${b.sub ? `<small>${esc(b.sub)}</small>` : ''}</button>`
  ).join('');
  box.querySelectorAll('.outcome').forEach(btn => btn.addEventListener('click', () => {
    pickState.outcome = btn.dataset.outcome;
    box.querySelectorAll('.outcome').forEach(x => x.classList.toggle('selected', x === btn));
  }));
}

$('#pick-group').addEventListener('change', renderOutcomePicker);
$('#pick-modal-close').addEventListener('click', () => $('#pick-modal').classList.add('hidden'));
$('#pick-modal').addEventListener('click', (e) => { if (e.target.id === 'pick-modal') $('#pick-modal').classList.add('hidden'); });

$('#pick-submit').addEventListener('click', async () => {
  const groupId = $('#pick-group').value;
  if (!groupId) return toast('Pick a group', 'Join or create a group first.', 'warn');
  if (!pickState.outcome) return toast('Pick an outcome', 'Choose a side first.', 'warn');
  try {
    await api(`${API.prediction}/picks`, {
      method: 'POST', auth: true,
      body: { group_id: groupId, match_id: pickState.matchId, predicted_outcome: pickState.outcome },
    });
    toast('Prediction placed', `${outcomeLabel(pickState.outcome)} locked in.`);
    $('#pick-modal').classList.add('hidden');
  } catch (err) { toastErr(err); }
});

/* ============================================================
   GROUPS
   ============================================================ */
async function loadGroups() {
  const grid = $('#groups-grid');
  grid.innerHTML = skeletons(3);
  try {
    const groups = await api(`${API.prediction}/groups/mine`, { auth: true });
    if (!groups.length) {
      grid.innerHTML = emptyState('👥', 'No groups yet', 'Create one above to start predicting.');
      return;
    }
    grid.innerHTML = sortGroups(groups).map(g => {
      const isDefault = g.id === DEFAULT_POOL_ID;
      const asian = g.bet_type === 'ASIAN';
      return `
      <div class="card group-card">
        <div class="gc-head">
          <h4>${esc(g.name)}</h4>
          <span class="badge ${asian ? 'asian' : 'european'}">${asian ? 'Asian HC' : '1X2'}</span>
        </div>
        <div class="gc-id">${esc(g.id)}</div>
        <div class="gc-meta">
          <span>${isDefault ? '🌍 Everyone is here' : (g.owner_user_id === store.user.id ? '👑 You own this' : '👤 Member')}</span>
          <button class="copy-id" data-copy="${esc(g.id)}">Copy ID</button>
        </div>
      </div>`;
    }).join('');
    grid.querySelectorAll('[data-copy]').forEach(b => b.addEventListener('click', () => {
      navigator.clipboard?.writeText(b.dataset.copy);
      toast('Copied', 'Group ID copied to clipboard.');
    }));
  } catch (err) {
    grid.innerHTML = emptyState('⚠️', 'Could not load groups', err.detail || '');
  }
}

$('#group-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = e.target.name.value.trim();
  const betType = e.target.bet_type.value;
  try {
    await api(`${API.prediction}/groups`, {
      method: 'POST', auth: true, body: { name, bet_type: betType },
    });
    toast('Group created', `"${name}" — ${betType === 'ASIAN' ? 'Asian handicap' : 'European 1X2'}.`);
    e.target.reset();
    loadGroups();
  } catch (err) { toastErr(err); }
});

$('#join-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const id = e.target.group_id.value.trim();
  try {
    await api(`${API.prediction}/groups/${encodeURIComponent(id)}/join`, { method: 'POST', auth: true });
    toast('Joined group', 'You are now a member.');
    e.target.reset();
    loadGroups();
  } catch (err) { toastErr(err); }
});

/* ============================================================
   PICKS
   ============================================================ */
async function loadPicks() {
  const tb = $('#picks-tbody');
  tb.innerHTML = `<tr><td colspan="6" style="padding:30px;text-align:center;color:var(--text-mute)">Loading…</td></tr>`;
  try {
    const [picks, fixtures, groups] = await Promise.all([
      api(`${API.prediction}/picks/mine`, { auth: true }),
      api(`${API.prediction}/fixtures`).catch(() => []),
      api(`${API.prediction}/groups/mine`, { auth: true }).catch(() => []),
    ]);
    const fx = Object.fromEntries(fixtures.map(f => [f.match_id, f]));
    const gx = Object.fromEntries(groups.map(g => [g.id, g.name]));
    if (!picks.length) {
      tb.innerHTML = `<tr><td colspan="6"><div class="empty"><span class="ee">🎯</span><p>No predictions yet — head to Matches.</p></div></td></tr>`;
      return;
    }
    tb.innerHTML = picks.map(p => {
      const m = fx[p.match_id];
      const matchLabel = m ? `${flag(m.home_team)} ${esc(m.home_team)} v ${esc(m.away_team)} ${flag(m.away_team)}` : `<span class="mono">${esc(p.match_id)}</span>`;
      const st = (p.status || '').toLowerCase();
      return `<tr>
        <td>${matchLabel}</td>
        <td>${esc(gx[p.group_id] || p.group_id)}</td>
        <td><strong>${outcomeLabel(p.predicted_outcome)}</strong></td>
        <td class="mono">${money(p.stake_minor)}</td>
        <td><span class="badge ${st || 'open'}">${esc(p.status || 'open')}</span></td>
        <td class="mono">${p.locked_at ? fmtDate(p.locked_at) : '—'}</td>
      </tr>`;
    }).join('');
  } catch (err) {
    tb.innerHTML = `<tr><td colspan="6" style="padding:30px;text-align:center;color:#ff8a8a">${esc(err.detail || 'Error')}</td></tr>`;
  }
}

/* ============================================================
   LEDGER
   ============================================================ */
$$('[data-ltab]').forEach(btn => btn.addEventListener('click', () => {
  $$('[data-ltab]').forEach(b => b.classList.toggle('active', b === btn));
  const t = btn.dataset.ltab;
  $$('.ltab').forEach(p => p.classList.add('hidden'));
  $(`#ltab-${t}`).classList.remove('hidden');
}));

// Ledger data is fetched once per load, then filtered per group client-side.
let ledgerData = { accounts: [], journal: [], audit: [], groups: [] };

async function loadLedger() {
  if (!ledgerData.groups.length) {
    try { ledgerData.groups = await api(`${API.prediction}/groups`, { auth: true }); }
    catch { ledgerData.groups = []; }
    $('#ledger-group').innerHTML = '<option value="">All groups</option>' +
      sortGroups(ledgerData.groups)
        .map(g => `<option value="${esc(g.id)}">${esc(g.name)}</option>`).join('');
  }
  $('#accounts-grid').innerHTML = skeletons(3);
  $('#journal-list').innerHTML = '<div class="skeleton" style="height:120px"></div>';
  try {
    const [accounts, journal, audit] = await Promise.all([
      api(`${API.ledger}/accounts`),
      api(`${API.ledger}/journal-entries`),
      api(`${API.ledger}/audit-log`),
    ]);
    ledgerData = { ...ledgerData, accounts, journal, audit };
    renderLedger();
  } catch (err) {
    $('#accounts-grid').innerHTML = emptyState('⚠️', 'Could not load ledger', err.detail || '');
  }
}

$('#ledger-group').addEventListener('change', renderLedger);

// Filter the ledger to one group: its pool account, the entries that touch it,
// and the accounts / audit rows involved in those entries.
function renderLedger() {
  const groupId = $('#ledger-group').value;
  let { accounts, journal, audit } = ledgerData;
  if (groupId) {
    const pool = accounts.find(a => a.owner_type === 'POOL' && a.owner_id === groupId);
    const poolId = pool ? pool.id : -1;
    journal = journal.filter(e => (e.postings || []).some(p => p.account_id === poolId));
    const acctIds = new Set(journal.flatMap(e => (e.postings || []).map(p => p.account_id)));
    if (pool) acctIds.add(poolId);
    accounts = accounts.filter(a => acctIds.has(a.id));
    const jids = new Set(journal.map(e => e.id));
    audit = audit.filter(r => jids.has(r.journal_entry_id));
  }
  renderAccounts(accounts);
  renderJournal(journal);
  renderAudit(audit);
}

function ledgerOwnerLabel(account) {
  const g = ledgerData.groups.find(x => x.id === account.owner_id);
  return g ? g.name : account.owner_id;
}

function renderAccounts(accounts) {
  const grid = $('#accounts-grid');
  if (!accounts.length) {
    grid.innerHTML = emptyState('📒', 'No accounts here yet', 'Accounts appear as the saga settles matches or deposits are recorded.');
    return;
  }
  grid.innerHTML = accounts.map(a => {
    const bal = a.balance_minor || 0;
    const cls = bal > 0 ? 'pos' : bal < 0 ? 'neg' : 'zero';
    return `<div class="card acct-card">
      <div class="ac-type">${esc(a.owner_type)}</div>
      <div class="ac-owner">${esc(ledgerOwnerLabel(a))}</div>
      <div class="ac-balance ${cls}">${bal < 0 ? '−' : ''}${money(Math.abs(bal))} <span style="font-size:13px;color:var(--text-mute)">${esc(a.currency || '')}</span></div>
    </div>`;
  }).join('');
}

function renderJournal(entries) {
  const list = $('#journal-list');
  if (!entries.length) {
    list.innerHTML = emptyState('🧾', 'No journal entries here', 'Settle a match or record a deposit to post a double-entry.');
    return;
  }
  list.innerHTML = entries.map(e => `
    <div class="journal-card">
      <div class="jc-head">
        <span class="jc-id">Entry #${e.id}</span>
        <span class="jc-time">${fmtDate(e.posted_at)}</span>
      </div>
      <div class="jc-reason">${esc(e.reason || '')}${e.match_id ? ` · match <span class="mono">${esc(e.match_id)}</span>` : ''}</div>
      ${(e.postings || []).map(p => `
        <div class="posting-row">
          <span><span class="dir ${p.direction}">${p.direction}</span> &nbsp;account #${p.account_id}</span>
          <span class="posting-amt">${money(p.amount_minor)}</span>
        </div>`).join('')}
    </div>`).join('');
}

function renderAudit(rows) {
  const tb = $('#audit-tbody');
  if (!rows.length) {
    tb.innerHTML = `<tr><td colspan="5"><div class="empty"><span class="ee">📑</span><p>No audit records here.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = rows.map(r => `<tr>
    <td class="mono">${r.id}</td>
    <td class="mono">#${r.journal_entry_id ?? '—'}</td>
    <td>${esc(r.actor || '')}</td>
    <td><span class="badge open">${esc(r.action || '')}</span></td>
    <td class="mono">${fmtDate(r.created_at)}</td>
  </tr>`).join('');
}

/* ============================================================
   ADMIN
   ============================================================ */
$('#save-key-btn').addEventListener('click', () => {
  store.adminKey = $('#admin-key').value.trim() || 'dev-admin-key-change-me';
  toast('Admin key saved', 'Stored in this browser.');
});

async function loadAdmin() {
  try {
    const [matches, groups] = await Promise.all([
      api(`${API.fixture}/fixtures`),
      api(`${API.prediction}/groups`, { auth: true }).catch(() => []),
    ]);
    const scheduled = matches.filter(m => (m.status || '').toLowerCase() === 'scheduled');
    fillSelect('#result-match', matches, m => `${m.home_team} v ${m.away_team} — ${m.status}`);
    fillSelect('#lock-match', scheduled.length ? scheduled : matches, m => `${m.home_team} v ${m.away_team}`);
    fillSelect('#kickoff-match', matches, m => `${m.home_team} v ${m.away_team} — ${m.status}`);
    fillSelect('#deposit-group', sortGroups(groups), g => g.name);
  } catch (err) { toastErr(err); }
}
function fillSelect(sel, items, label) {
  const el = $(sel);
  el.innerHTML = items.length
    ? items.map(m => `<option value="${esc(m.id)}">${esc(label(m))}</option>`).join('')
    : '<option value="">No matches</option>';
}

$('#admin-sync').addEventListener('click', async (e) => {
  e.target.disabled = true;
  try {
    const r = await api(`${API.fixture}/admin/sync`, { method: 'POST', adminKey: true });
    toast('Sync complete', `${r.fixtures_created} fixtures created, ${r.odds_refreshed} odds refreshed.`);
    loadAdmin();
  } catch (err) { toastErr(err); }
  finally { e.target.disabled = false; }
});

$('#admin-result').addEventListener('click', async (e) => {
  const matchId = $('#result-match').value;
  const home = parseInt($('#result-home').value, 10);
  const away = parseInt($('#result-away').value, 10);
  if (!matchId) return toast('Pick a match', '', 'warn');
  if (Number.isNaN(home) || Number.isNaN(away)) return toast('Enter both scores', '', 'warn');
  e.target.disabled = true;
  try {
    const r = await api(`${API.fixture}/admin/matches/${encodeURIComponent(matchId)}/result`, {
      method: 'POST', adminKey: true, body: { home_score: home, away_score: away },
    });
    toast('Match settled', `Event ${String(r.event_id).slice(0, 12)}… emitted to the saga.`);
    loadAdmin();
  } catch (err) { toastErr(err); }
  finally { e.target.disabled = false; }
});

$('#admin-lock').addEventListener('click', async (e) => {
  const matchId = $('#lock-match').value;
  if (!matchId) return toast('Pick a match', '', 'warn');
  e.target.disabled = true;
  try {
    const r = await api(`${API.prediction}/admin/matches/${encodeURIComponent(matchId)}/force-lock`, {
      method: 'POST', adminKey: true,
    });
    toast('Picks locked', `${r.events_published} PickLocked event(s) published.`);
  } catch (err) { toastErr(err); }
  finally { e.target.disabled = false; }
});

$('#admin-kickoff').addEventListener('click', async (e) => {
  const matchId = $('#kickoff-match').value;
  const val = $('#kickoff-time').value;
  if (!matchId || !val) return toast('Pick a match and time', '', 'warn');
  e.target.disabled = true;
  try {
    await api(`${API.fixture}/admin/matches/${encodeURIComponent(matchId)}/kickoff`, {
      method: 'PUT', adminKey: true, body: { kickoff_at: new Date(val).toISOString() },
    });
    toast('Kickoff updated', '');
    loadAdmin();
  } catch (err) { toastErr(err); }
  finally { e.target.disabled = false; }
});

$('#deposit-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const groupId = $('#deposit-group').value;
  const depositor = $('#deposit-depositor').value.trim();
  const amount = parseInt($('#deposit-amount').value, 10);
  if (!groupId) return toast('Pick a group', '', 'warn');
  if (!depositor) return toast('Enter a depositor', '', 'warn');
  if (!Number.isFinite(amount) || amount <= 0) return toast('Enter a positive amount', '', 'warn');
  const btn = e.submitter || e.target.querySelector('button');
  btn.disabled = true;
  try {
    await api(`${API.ledger}/admin/deposits`, {
      method: 'POST', adminKey: true,
      body: { group_id: groupId, depositor, amount_minor: amount },
    });
    toast('Deposit recorded', `${depositor} → pool credited ${amount.toLocaleString('en-US')} minor units.`);
    e.target.reset();
  } catch (err) { toastErr(err); }
  finally { btn.disabled = false; }
});

/* ============================================================
   Shared render helpers
   ============================================================ */
function skeletons(n) {
  return Array.from({ length: n }, () => '<div class="skeleton"></div>').join('');
}
function emptyState(emoji, title, detail) {
  return `<div class="empty"><span class="ee">${emoji}</span><p><strong>${esc(title)}</strong></p>${detail ? `<p style="font-size:12.5px;margin-top:4px">${esc(detail)}</p>` : ''}</div>`;
}

/* ============================================================
   Boot
   ============================================================ */
if (store.token && store.user) enterApp();
