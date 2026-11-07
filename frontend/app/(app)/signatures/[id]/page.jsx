"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { errorMessage } from "@/lib/api";
import { useSignatureCertificate } from "@/lib/queries";
import { SignatureBadge } from "@/components/Signature";
import { ErrorNote, Loading } from "@/components/States";

/** Full timestamp for a record: local time with zone, plus UTC. */
function stamp(v) {
  if (!v) return "—";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "—";
  const local = d.toLocaleString("en-IN", {
    day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit", second: "2-digit", timeZoneName: "short",
  });
  return `${local} (${d.toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC")})`;
}

const EVENT_LABEL = {
  created: "Sent for signing",
  link_reissued: "New signing link issued",
  viewed: "Opened the document",
  signed: "Signed",
  declined: "Declined to sign",
  completed: "Completed — everyone signed",
  cancelled: "Cancelled",
};

/** Shorten a user agent to something readable, keeping the full string on hover. */
function browser(ua) {
  if (!ua) return "—";
  const name = /Edg\//.test(ua) ? "Edge" : /OPR\//.test(ua) ? "Opera" : /Chrome\//.test(ua) ? "Chrome" : /Firefox\//.test(ua) ? "Firefox" : /Safari\//.test(ua) ? "Safari" : null;
  const os = /Windows/.test(ua) ? "Windows" : /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iOS" : /Mac OS X/.test(ua) ? "macOS" : /Linux/.test(ua) ? "Linux" : null;
  return name && os ? `${name} on ${os}` : ua.slice(0, 60);
}

function Field({ label, children, mono }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs font-semibold uppercase tracking-wide text-faint">{label}</dt>
      <dd className={`mt-0.5 break-words ${mono ? "font-mono text-xs" : "text-sm"}`}>{children}</dd>
    </div>
  );
}

export default function CertificatePage() {
  const { id } = useParams();
  const { data: env, isLoading, error, refetch } = useSignatureCertificate(id);

  if (isLoading) return <Loading label="Loading the certificate…" />;
  if (error) return <ErrorNote message={errorMessage(error, "Couldn't load this signature record.")} onRetry={refetch} />;

  const completed = env.status === "completed";

  return (
    <div className="mx-auto max-w-3xl">
      <div className="no-print mb-6 flex flex-wrap items-center justify-between gap-3">
        <Link href={`/contracts/${env.contract_id}`} className="text-sm font-semibold text-muted hover:text-ink">
          ← Back to the contract
        </Link>
        <button type="button" className="btn btn-quiet px-3 py-1.5" onClick={() => window.print()}>
          Print or save as PDF
        </button>
      </div>

      <article className="rounded-xl border border-rule bg-page p-6 sm:p-10 print:border-0 print:p-0">
        <header className="flex flex-wrap items-start justify-between gap-3 border-b border-rule pb-6">
          <div className="min-w-0">
            <p className="text-sm font-semibold uppercase tracking-wide text-faint">
              {completed ? "Signature certificate" : "Signing audit trail"}
            </p>
            <h1 className="mt-2 break-words text-3xl">{env.document_filename}</h1>
          </div>
          <SignatureBadge status={env.status} className="mt-1" />
        </header>

        <dl className="mt-6 grid gap-4 sm:grid-cols-2">
          <Field label="Sent by">{env.requested_by_name}</Field>
          <Field label="Sent">{stamp(env.created_at)}</Field>
          <Field label={completed ? "Completed" : env.status === "pending" ? "Status" : "Closed"}>
            {env.status === "pending" ? `Waiting — ${env.signed_count} of ${env.signers.length} signed` : stamp(env.closed_at)}
          </Field>
          <Field label="Record ID" mono>
            {env.id}
          </Field>
          <div className="sm:col-span-2">
            <Field label="Document fingerprint (SHA-256)" mono>
              {env.document_sha256}
            </Field>
          </div>
        </dl>
        {env.message && (
          <p className="mt-4 whitespace-pre-wrap break-words rounded-md bg-bg px-3 py-2 text-sm">
            <span className="font-semibold">Message to signers:</span> {env.message}
          </p>
        )}

        <h2 className="mt-10 text-xl">Signers</h2>
        <ol className="mt-4 space-y-5">
          {env.signers.map((s) => (
            <li key={s.id} className="break-inside-avoid rounded-lg border border-rule p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-semibold">
                  {s.name} <span className="font-normal text-muted">· {s.email}</span>
                </p>
                <span className={`text-sm font-semibold ${s.status === "signed" ? "text-ok" : s.status === "declined" ? "text-danger" : "text-faint"}`}>
                  {s.status === "signed" ? "Signed" : s.status === "declined" ? "Declined" : "Not signed yet"}
                </span>
              </div>
              {s.status === "signed" && (
                <div className="mt-3 border-b border-ink/60 pb-1">
                  <p className="truncate text-5xl leading-tight" style={{ fontFamily: "var(--font-signature)" }}>
                    {s.typed_signature}
                  </p>
                </div>
              )}
              {s.decline_reason && <p className="mt-3 text-sm">Reason: &ldquo;{s.decline_reason}&rdquo;</p>}
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <Field label="Opened">{stamp(s.viewed_at)}</Field>
                <Field label={s.status === "declined" ? "Declined" : "Signed"}>{stamp(s.acted_at)}</Field>
                <Field label="IP address">{s.ip_address || "—"}</Field>
                <Field label="Browser">
                  <span title={s.user_agent || ""}>{browser(s.user_agent)}</span>
                </Field>
              </dl>
              {s.consent_text && <p className="mt-3 text-xs text-muted">Agreed to: &ldquo;{s.consent_text}&rdquo;</p>}
            </li>
          ))}
        </ol>

        <h2 className="mt-10 text-xl">Audit trail</h2>
        <ol className="mt-4 divide-y divide-rule border-y border-rule text-sm">
          {(env.events || []).map((e, i) => (
            <li key={i} className="grid gap-1 py-2.5 sm:grid-cols-[15rem_minmax(0,1fr)] sm:gap-4">
              <span className="text-xs text-muted">{stamp(e.created_at)}</span>
              <span className="min-w-0">
                <span className="font-medium">{EVENT_LABEL[e.type] || e.type}</span>
                {e.actor && <span> · {e.actor}</span>}
                {e.detail && <span className="block break-words text-muted">{e.detail}</span>}
                {e.ip_address && (
                  <span className="block text-xs text-faint" title={e.user_agent || ""}>
                    {e.ip_address} · {browser(e.user_agent)}
                  </span>
                )}
              </span>
            </li>
          ))}
        </ol>

        <p className="mt-8 text-xs text-faint">
          Each signer opened a private link, typed their name and agreed to sign electronically. The fingerprint above is the
          SHA-256 of the exact file that was sent; anyone can check a copy against it (for example with{" "}
          <code>sha256sum</code>). This is a simple electronic signature with an audit trail, not an Aadhaar eSign or
          certificate-based digital signature. Whether it is enough for a particular document depends on the law that applies
          to it.
        </p>
      </article>
    </div>
  );
}
