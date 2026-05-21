// Thin fetch wrapper. Every call goes through the gateway, which fans out to
// the four backend services by URL prefix.
const BASE = {
  prediction: '/api/prediction',
  fixture: '/api/fixture',
  ledger: '/api/ledger',
  bff: '/api/bff',
};

export class ApiError extends Error {
  constructor(status, body) {
    const message =
      typeof body === 'string'
        ? body
        : body?.detail || body?.message || 'request failed';
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

function authToken() {
  return localStorage.getItem('token');
}

async function request(service, path, { method = 'GET', body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth && authToken()) headers.Authorization = `Bearer ${authToken()}`;

  const res = await fetch(`${BASE[service]}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!res.ok) throw new ApiError(res.status, data);
  return data;
}

export const api = {
  prediction: (path, opts) => request('prediction', path, opts),
  fixture: (path, opts) => request('fixture', path, opts),
  ledger: (path, opts) => request('ledger', path, opts),
  bff: (path, opts) => request('bff', path, opts),
};
