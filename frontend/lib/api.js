import axios from "axios";
import { clearSession, getToken } from "./session";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

const api = axios.create({ baseURL: `${API_URL}/api/v1`, timeout: 60000 });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// A 401 on anything but login/register means the session expired: sign out
// and send the user to the sign-in page, remembering where they were.
api.interceptors.response.use(undefined, (err) => {
  const url = err.config?.url || "";
  // Only a request that carried a token can mean "session expired"; a
  // signed-out request is the page guard's job, not this one.
  const hadToken = Boolean(err.config?.headers?.Authorization);
  if (err.response?.status === 401 && hadToken && !url.includes("/auth/login") && !url.includes("/auth/register")) {
    clearSession();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      const next = encodeURIComponent(window.location.pathname);
      window.location.href = `/login?expired=1&next=${next}`;
    }
  }
  return Promise.reject(err);
});

/** Turn any FastAPI / network error into one readable sentence. */
export function errorMessage(err, fallback = "Something went wrong.") {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg.replace(/^Value error, /, "");
  if (err && !err.response) {
    return "The server isn't answering. It sleeps when idle and takes about a minute to wake — try again shortly.";
  }
  return fallback;
}

const qs = (params) => {
  const clean = Object.fromEntries(Object.entries(params || {}).filter(([, v]) => v !== undefined && v !== null && v !== ""));
  const s = new URLSearchParams(clean).toString();
  return s ? `?${s}` : "";
};

const data = (p) => p.then((r) => r.data);

export const authAPI = {
  login: (email, password) => data(api.post("/auth/login", { email, password })),
  register: (body) => data(api.post("/auth/register", body)),
  me: () => data(api.get("/auth/me")),
};

export const contractsAPI = {
  list: (params) => data(api.get(`/contracts${qs(params)}`)).then((d) => (Array.isArray(d) ? d : d?.contracts || [])),
  stats: () => data(api.get("/contracts/stats")),
  get: (id) => data(api.get(`/contracts/${id}`)),
  upload: (file, onProgress) => {
    const form = new FormData();
    form.append("file", file);
    return data(
      api.post("/contracts/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (e) => e.total && onProgress?.(Math.round((e.loaded * 100) / e.total)),
      }),
    );
  },
  reanalyze: (id) => data(api.post(`/contracts/${id}/analyze`)),
  remove: (id) => data(api.delete(`/contracts/${id}`)),
};

export const analysisAPI = {
  // 404 means "not analysed yet", not an error.
  forContract: (contractId) =>
    data(api.get(`/analysis/contract/${contractId}`)).catch((err) => {
      if (err?.response?.status === 404) return null;
      throw err;
    }),
};

export const obligationsAPI = {
  list: (params) => data(api.get(`/obligations${qs(params)}`)),
  stats: () => data(api.get("/obligations/stats")),
  complete: (id) => data(api.patch(`/obligations/${id}/complete`)),
  update: (id, patch) => data(api.patch(`/obligations/${id}`, patch)),
  remove: (id) => data(api.delete(`/obligations/${id}`)),
};

export const alertsAPI = {
  list: (params) => data(api.get(`/alerts${qs(params)}`)),
  stats: () => data(api.get("/alerts/stats")),
  markRead: (id) => data(api.patch(`/alerts/${id}/read`)),
  markAllRead: () => data(api.post("/alerts/mark-all-read")),
  dismiss: (id) => data(api.delete(`/alerts/${id}`)),
};

export default api;