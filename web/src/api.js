// API client. Every call goes through the API, so role, region, masking and audit rules apply.
// The desktop session token lives in sessionStorage (gone when the tab closes); the inspector app
// keeps its own token inside its encrypted store.

const BASE = "/api";
let token = sessionStorage.getItem("vg_token");
let user = JSON.parse(sessionStorage.getItem("vg_user") || "null");
const listeners = new Set();

export function session() {
  return { token, user };
}

export function onSessionChange(fn) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

function setSession(t, u) {
  token = t;
  user = u;
  if (t) {
    sessionStorage.setItem("vg_token", t);
    sessionStorage.setItem("vg_user", JSON.stringify(u));
  } else {
    sessionStorage.removeItem("vg_token");
    sessionStorage.removeItem("vg_user");
  }
  listeners.forEach((fn) => fn({ token, user }));
}

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function request(path, { method = "GET", body, form, tokenOverride, raw } = {}) {
  const headers = {};
  const auth = tokenOverride ?? token;
  if (auth) headers.Authorization = `Bearer ${auth}`;
  let payload;
  if (form) payload = form;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const res = await fetch(BASE + path, { method, headers, body: payload });
  if (raw) {
    if (!res.ok) throw new ApiError(res.status, "error", res.statusText);
    return res;
  }
  const data = res.headers.get("content-type")?.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const err = new ApiError(res.status, data?.code || "error", data?.message || res.statusText);
    if (res.status === 401 && !tokenOverride && token) setSession(null, null);
    throw err;
  }
  return data;
}

export async function signIn(username, password) {
  const data = await request("/auth/token", { method: "POST", body: { username, password } });
  setSession(data.access_token, data.user);
  return data;
}

// Demo only (DEMO_MODE on): one-click sign-in as a test account from the role cards.
export async function signInDemo(username) {
  const data = await request("/auth/demo-token", { method: "POST", body: { username }, tokenOverride: "" });
  setSession(data.access_token, data.user);
  return data;
}

export async function signOut() {
  try {
    await request("/auth/sign-out", { method: "POST" });
  } catch {
    /* already signed out */
  }
  setSession(null, null);
}

export const get = (path) => request(path);
export const post = (path, body) => request(path, { method: "POST", body });
export const put = (path, body) => request(path, { method: "PUT", body });
export const patch = (path, body) => request(path, { method: "PATCH", body });

// Long jobs: start, then poll the job status (quick tunnels carry no server-sent events).
export async function pollJob(jobId, onUpdate, intervalMs = 1500) {
  for (;;) {
    const job = await get(`/jobs/${jobId}`);
    onUpdate?.(job);
    if (job.status === "done" || job.status === "failed") return job;
    await new Promise((r) => setTimeout(r, intervalMs));
  }
}
