import axios from "axios";
import { clearSession, getToken } from "./session";
import { getWorkspaceId, setWorkspaceId } from "./workspace";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/+$/, "");

const api = axios.create({ baseURL: `${API_URL}/api/v1`, timeout: 60000 });

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Scope data requests to the selected workspace. /workspaces/{id}/... routes
  // name their workspace in the path instead; invite and signing links aren't
  // tied to whichever workspace the visitor has selected.
  const workspaceId = getWorkspaceId();
  const url = config.url || "";
  if (workspaceId && !["/workspaces", "/invites", "/sign/"].some((p) => url.startsWith(p))) {
    config.headers["X-Workspace-Id"] = workspaceId;
  }
  return config;
});

// A 401 on anything but login/register means the session expired: sign out
// and send the user to the sign-in page, remembering where they were.
api.interceptors.response.use(undefined, (err) => {
  const url = err.config?.url || "";
  // The selected workspace was deleted or we were removed from it: fall back
  // to the personal workspace instead of showing errors everywhere.
  if (err.response?.status === 404 && err.response?.data?.detail === "Workspace not found" && err.config?.headers?.["X-Workspace-Id"]) {
    setWorkspaceId(null);
  }
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
  // 404 means "not analysed yet", not an error .
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

export const workspacesAPI = {
  list: () => data(api.get("/workspaces")),
  create: (name) => data(api.post("/workspaces", { name })),
  rename: (id, name) => data(api.patch(`/workspaces/${id}`, { name })),
  remove: (id) => data(api.delete(`/workspaces/${id}`)),
  members: (id) => data(api.get(`/workspaces/${id}/members`)),
  setRole: (id, userId, role) => data(api.patch(`/workspaces/${id}/members/${userId}`, { role })),
  removeMember: (id, userId) => data(api.delete(`/workspaces/${id}/members/${userId}`)),
  invites: (id) => data(api.get(`/workspaces/${id}/invites`)),
  createInvite: (id, body) => data(api.post(`/workspaces/${id}/invites`, body)),
  revokeInvite: (id, inviteId) => data(api.delete(`/workspaces/${id}/invites/${inviteId}`)),
};

export const approvalsAPI = {
  list: (params) => data(api.get(`/approvals${qs(params)}`)),
  stats: () => data(api.get("/approvals/stats")),
  forContract: (contractId) => data(api.get(`/approvals/contract/${contractId}`)),
  request: (contractId, body) => data(api.post(`/approvals/contract/${contractId}`, body)),
  decide: (id, decision, comment) => data(api.post(`/approvals/${id}/decision`, { decision, comment })),
  cancel: (id) => data(api.post(`/approvals/${id}/cancel`)),
};

export const signaturesAPI = {
  forContract: (contractId) => data(api.get(`/signatures/contract/${contractId}`)),
  send: (contractId, body) => data(api.post(`/signatures/contract/${contractId}`, body)),
  get: (id) => data(api.get(`/signatures/${id}`)),
  newLink: (id, signerId) => data(api.post(`/signatures/${id}/signers/${signerId}/link`)),
  cancel: (id) => data(api.post(`/signatures/${id}/cancel`)),
  signedPdf: (id) => api.get(`/signatures/${id}/signed-pdf`, { responseType: "blob", timeout: 120000 }),
};

/** Public signing routes: no account needed, the token in the link is the key. */
export const signingAPI = {
  get: (token) => data(api.get(`/sign/${encodeURIComponent(token)}`)),
  documentUrl: (token) => `${API_URL}/api/v1/sign/${encodeURIComponent(token)}/document`,
  sign: (token, body) => data(api.post(`/sign/${encodeURIComponent(token)}/sign`, body)),
  signedPdfUrl: (token) => `${API_URL}/api/v1/sign/${encodeURIComponent(token)}/signed-pdf`,
  decline: (token, reason) => data(api.post(`/sign/${encodeURIComponent(token)}/decline`, { reason })),
};

/** Save a blob response as a file, using the server's filename when it sends one. */
export function saveBlob(res, fallbackName) {
  const cd = res.headers?.["content-disposition"] || "";
  const m = cd.match(/filename\*=UTF-8''([^;]+)/i);
  const name = m ? decodeURIComponent(m[1]) : fallbackName;
  const url = URL.createObjectURL(res.data);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Where a signer opens their link. */
export const signingLink = (token) =>
  `${typeof window !== "undefined" ? window.location.origin : ""}/sign/${encodeURIComponent(token)}`;

export const invitesAPI = {
  preview: (token) => data(api.get(`/invites/${encodeURIComponent(token)}`)),
  accept: (token) => data(api.post(`/invites/${encodeURIComponent(token)}/accept`)),
};

export default api;