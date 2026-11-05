// Fetch client with session persistence and proactive JWT refresh (report module 1 & 2).
const SESSION_KEY = 'alumni-connect.auth-session';
const REFRESH_BUFFER_SECONDS = 60;

let session = null;
let refreshing = null;

export function loadSession() {
  if (session) return session;
  try {
    session = JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    session = null;
  }
  return session;
}

export function saveSession(next) {
  session = next;
  if (next) localStorage.setItem(SESSION_KEY, JSON.stringify(next));
  else localStorage.removeItem(SESSION_KEY);
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function parse(res) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    let detail = data?.detail;
    if (Array.isArray(detail)) detail = detail.map((d) => d.msg).join('; ');
    throw new ApiError(detail || `Request failed (${res.status})`, res.status);
  }
  return data;
}

async function ensureFresh() {
  const s = loadSession();
  if (!s || s.expires_at > Math.floor(Date.now() / 1000) + REFRESH_BUFFER_SECONDS) return;
  refreshing ??= fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: s.refresh_token }),
  })
    .then(parse)
    .then(saveSession)
    .catch((err) => {
      saveSession(null);
      throw err;
    })
    .finally(() => {
      refreshing = null;
    });
  await refreshing;
}

async function request(path, { method = 'GET', json, form, auth = true } = {}) {
  const headers = {};
  if (auth) {
    await ensureFresh();
    const s = loadSession();
    if (s) headers.Authorization = `Bearer ${s.access_token}`;
  }
  let body;
  if (json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(json);
  } else if (form) {
    body = form;
  }
  return parse(await fetch(path, { method, headers, body }));
}

export const api = {
  signup: (data) => request('/api/auth/signup', { method: 'POST', json: data, auth: false }),
  login: (data) => request('/api/auth/login', { method: 'POST', json: data, auth: false }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),

  alumni: () => request('/api/alumni'),
  createAlumnus: (data) => request('/api/alumni', { method: 'POST', json: data }),
  updateAlumnus: (id, data) => request(`/api/alumni/${id}`, { method: 'PATCH', json: data }),
  deleteAlumnus: (id) => request(`/api/alumni/${id}`, { method: 'DELETE' }),

  requests: () => request('/api/mentorship'),
  requestMentorship: (alumni_profile_id, message) =>
    request('/api/mentorship', { method: 'POST', json: { alumni_profile_id, message } }),
  resolveRequest: (id, status) => request(`/api/mentorship/${id}`, { method: 'PATCH', json: { status } }),

  events: () => request('/api/events'),
  createEvent: (form) => request('/api/events', { method: 'POST', form }),
  rsvp: (id) => request(`/api/events/${id}/rsvp`, { method: 'POST' }),
  deleteEvent: (id) => request(`/api/events/${id}`, { method: 'DELETE' }),

  notifications: () => request('/api/notifications'),
  markRead: (id) => request(`/api/notifications/${id}/read`, { method: 'POST' }),
  markAllRead: () => request('/api/notifications/read-all', { method: 'POST' }),

  stats: () => request('/api/stats'),
};
