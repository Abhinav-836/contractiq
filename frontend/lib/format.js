const toDate = (v) => {
  if (!v) return null;
  // The API returns naive UTC timestamps ("2026-11-04T05:43:47"); treat them as UTC.
  const s = typeof v === "string" && /T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(v) ? `${v}Z` : v;
  const d = new Date(s);
  return Number.isNaN(d.getTime()) ? null : d;
};

export function formatDate(v) {
  const d = toDate(v);
  return d ? d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";
}

export function formatDateTime(v) {
  const d = toDate(v);
  return d ? d.toLocaleString("en-IN", { day: "numeric", month: "short", hour: "numeric", minute: "2-digit" }) : "—";
}

export function timeAgo(v) {
  const d = toDate(v);
  if (!d) return "—";
  const s = Math.round((Date.now() - d.getTime()) / 1000);
  if (s < 60) return "just now";
  const units = [
    [60, "minute"],
    [24, "hour"],
    [30, "day"],
    [12, "month"],
    [Infinity, "year"],
  ];
  let n = s / 60;
  for (const [step, unit] of units) {
    if (n < step) {
      const r = Math.floor(n);
      return `${r} ${unit}${r === 1 ? "" : "s"} ago`;
    }
    n /= step;
  }
  return formatDate(v);
}

export function fileSize(bytes) {
  if (!bytes) return "0 KB";
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export const fileKind = (c) => (c?.file_type || "").replace(".", "").toUpperCase() || "FILE";

/*
 * Obligation due dates come straight from contract text and are usually
 * relative ("Within 45 days"), not ISO dates — show them as written.
 */
export function formatDue(value) {
  if (!value) return null;
  if (/^\d{4}-\d{2}-\d{2}/.test(value)) return formatDate(value);
  return value;
}

/** Sort key in days: real dates by distance from now, "within N units" by N, unknown last. */
export function dueSortKey(value) {
  if (!value) return Number.POSITIVE_INFINITY;
  if (/^\d{4}-\d{2}-\d{2}/.test(value)) {
    const d = toDate(value);
    if (d) return (d.getTime() - Date.now()) / 86400000;
  }
  const m = /(\d+)\s*(hour|day|week|month|year)/i.exec(value);
  if (m) return Number(m[1]) * { hour: 1 / 24, day: 1, week: 7, month: 30, year: 365 }[m[2].toLowerCase()];
  return Number.MAX_SAFE_INTEGER;
}

export const RISK = {
  high: { label: "High risk", short: "High" },
  medium: { label: "Medium risk", short: "Medium" },
  low: { label: "Low risk", short: "Low" },
  not_contract: { label: "Not a contract", short: "—" },
};

export const riskKey = (level) => {
  const l = String(level || "").toLowerCase();
  return RISK[l] ? l : null;
};

export const STATUS = {
  processing: "Reviewing",
  completed: "Reviewed",
  failed: "Review failed",
};