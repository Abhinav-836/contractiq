"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { errorMessage, signingAPI } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { track } from "@/lib/track";
import Logo from "@/components/Logo";
import { Loading, Spinner } from "@/components/States";

const norm = (s) => (s || "").trim().replace(/\s+/g, " ").toLowerCase();

function Progress({ signers, closed }) {
  return (
    <ul className="mt-2 space-y-1.5 text-sm">
      {signers.map((s, i) => (
        <li key={i} className="flex items-baseline gap-2">
          <span
            aria-hidden="true"
            className={`w-3 shrink-0 font-semibold ${s.status === "signed" ? "text-ok" : s.status === "declined" ? "text-danger" : "text-faint"}`}
          >
            {s.status === "signed" ? "✓" : s.status === "declined" ? "✕" : "•"}
          </span>
          <span className="min-w-0 flex-1 truncate">
            {s.name}
            {s.is_you && <span className="text-faint"> (you)</span>}
          </span>
          <span className="shrink-0 text-faint">{s.status === "pending" ? (closed ? "Not signed" : "Waiting") : s.status === "signed" ? "Signed" : "Declined"}</span>
        </li>
      ))}
    </ul>
  );
}

function Document({ token, filename }) {
  const url = signingAPI.documentUrl(token);
  const isPdf = /\.pdf$/i.test(filename);
  // Phones often can't show a PDF inside a page, so they get a button instead.
  return (
    <div>
      {isPdf && (
        <iframe
          src={url}
          title={filename}
          className="hidden h-[70vh] min-h-[480px] w-full rounded-lg border border-rule bg-white lg:block"
        />
      )}
      <div className={`rounded-lg border border-dashed border-rule bg-page px-4 py-6 text-center ${isPdf ? "lg:hidden" : ""}`}>
        <p className="text-muted">Read the document before you sign.</p>
        <a href={url} target="_blank" rel="noopener noreferrer" className="btn btn-quiet mt-3">
          Open {filename}
        </a>
      </div>
      {isPdf && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-2 hidden text-sm font-semibold text-pen underline-offset-4 hover:underline lg:inline-block"
        >
          Open {filename} in a new tab
        </a>
      )}
    </div>
  );
}

function SignForm({ token, info, onDone }) {
  const [typed, setTyped] = useState("");
  const [consent, setConsent] = useState(false);
  const [declining, setDeclining] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const matches = norm(typed) === norm(info.signer.name);

  const sign = async (e) => {
    e.preventDefault();
    if (!matches) return setError(`Type your full name exactly as shown: ${info.signer.name}`);
    if (!consent) return setError("Tick the box to agree to sign electronically.");
    setBusy(true);
    setError("");
    try {
      const res = await signingAPI.sign(token, { typed_name: typed, consent: true });
      track("document_signed");
      onDone(res);
    } catch (err) {
      setError(errorMessage(err, "Couldn't record your signature."));
      setBusy(false);
    }
  };

  const decline = async (e) => {
    e.preventDefault();
    if (!reason.trim()) return setError("Say why you're declining so the sender knows what to change.");
    setBusy(true);
    setError("");
    try {
      const res = await signingAPI.decline(token, reason.trim());
      track("document_declined");
      onDone(res);
    } catch (err) {
      setError(errorMessage(err, "Couldn't record that."));
      setBusy(false);
    }
  };

  if (declining) {
    return (
      <form onSubmit={decline} noValidate className="rounded-xl border border-rule bg-page p-5">
        <h2 className="text-xl">Decline to sign</h2>
        <p className="mt-1 text-sm text-muted">
          This stops the signing for everyone. {info.requested_by_name || "The sender"} will see your reason.
        </p>
        <label htmlFor="reason" className="sr-only">
          Reason
        </label>
        <textarea
          id="reason"
          className="field mt-3 resize-y"
          rows={3}
          maxLength={2000}
          placeholder="What needs to change?"
          value={reason}
          onChange={(e) => {
            setReason(e.target.value);
            setError("");
          }}
        />
        {error && (
          <p role="alert" className="mt-2 text-sm text-danger">
            {error}
          </p>
        )}
        <div className="mt-4 flex gap-2">
          <button type="submit" className="btn btn-danger flex-1" disabled={busy}>
            {busy && <Spinner />} Decline
          </button>
          <button type="button" className="btn btn-quiet" onClick={() => setDeclining(false)} disabled={busy}>
            Back
          </button>
        </div>
      </form>
    );
  }

  return (
    <form onSubmit={sign} noValidate className="rounded-xl border border-rule bg-page p-5">
      <h2 className="text-xl">Sign</h2>
      <label htmlFor="typed" className="mb-1.5 mt-3 block text-sm font-medium">
        Type your full name: <span className="font-semibold">{info.signer.name}</span>
      </label>
      <input
        id="typed"
        className="field"
        autoComplete="name"
        maxLength={120}
        value={typed}
        aria-invalid={Boolean(error) && !matches}
        onChange={(e) => {
          setTyped(e.target.value);
          setError("");
        }}
      />
      <div
        aria-hidden="true"
        className="mt-3 flex h-20 items-end border-b-2 border-ink/70 px-2 pb-1"
        style={{ fontFamily: "var(--font-signature)" }}
      >
        <span className={`truncate text-5xl leading-none ${typed.trim() ? "text-ink" : "text-faint/50"}`}>
          {typed.trim() || info.signer.name}
        </span>
      </div>
      <p className="mt-1 text-xs text-faint">Your signature</p>

      <label className="mt-4 flex cursor-pointer items-start gap-3 text-sm">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => {
            setConsent(e.target.checked);
            setError("");
          }}
          className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--pen)]"
        />
        <span>{info.consent_text}</span>
      </label>

      {error && (
        <p role="alert" className="mt-3 text-sm text-danger">
          {error}
        </p>
      )}
      <button type="submit" className="btn btn-primary mt-5 w-full py-3" disabled={busy}>
        {busy && <Spinner />} {busy ? "Signing…" : "Sign document"}
      </button>
      <button
        type="button"
        className="mt-3 w-full text-sm font-semibold text-muted underline-offset-4 hover:text-danger hover:underline"
        onClick={() => {
          setDeclining(true);
          setError("");
        }}
        disabled={busy}
      >
        Decline to sign…
      </button>
      <p className="mt-4 text-xs text-faint">
        We record the time, your IP address and browser with your signature, and a fingerprint (SHA-256) of the document so
        it can be shown later exactly what was signed.
      </p>
    </form>
  );
}

function Outcome({ info }) {
  const me = info.signer;
  const status = info.envelope_status;
  let title, body;
  if (me.status === "signed") {
    title = "You signed this document";
    body =
      status === "completed"
        ? "Everyone has signed. The sender has the signature certificate."
        : "Thanks. We're waiting for the others to sign.";
  } else if (me.status === "declined") {
    title = "You declined to sign";
    body = "The sender can see your reason and may send a new version.";
  } else if (status === "cancelled") {
    title = "This signing request was cancelled";
    body = "The sender cancelled it, so there's nothing to sign. If you think that's a mistake, ask them for a new link.";
  } else if (status === "declined") {
    title = "Signing was stopped";
    body = "Someone declined to sign, so this request is closed. The sender may send a new version.";
  } else {
    title = "This signing request is closed";
    body = "";
  }
  return (
    <div className="rounded-xl border border-rule bg-page p-5">
      <h2 className="text-xl">{title}</h2>
      {body && <p className="mt-2 text-muted">{body}</p>}
      {me.status === "signed" && (
        <div className="mt-4">
          <p className="text-4xl leading-none" style={{ fontFamily: "var(--font-signature)" }}>
            {me.typed_signature}
          </p>
          <p className="mt-2 text-sm text-muted">Signed {formatDateTime(me.acted_at)}</p>
        </div>
      )}
      {me.status === "declined" && me.decline_reason && (
        <p className="mt-3 rounded-md bg-bg px-3 py-2 text-sm">&ldquo;{me.decline_reason}&rdquo;</p>
      )}
    </div>
  );
}

export default function SigningPage() {
  const { token } = useParams();
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["signing", token],
    queryFn: () => signingAPI.get(token),
    enabled: Boolean(token),
    retry: false,
  });
  const info = q.data;

  useEffect(() => {
    if (info?.document_filename) document.title = `Sign ${info.document_filename} · ContractIQ`;
  }, [info?.document_filename]);

  let body;
  if (q.isLoading) {
    body = <Loading label="Opening the document…" />;
  } else if (q.error) {
    body = (
      <div className="mx-auto max-w-md">
        <h1 className="text-3xl">This signing link doesn&apos;t work</h1>
        <p className="mt-3 text-muted">
          {q.error?.response?.status === 404
            ? "It may have been replaced by a newer link, or the document was removed. Ask whoever sent it for a new link."
            : errorMessage(q.error)}
        </p>
      </div>
    );
  } else {
    const canAct = info.envelope_status === "pending" && info.signer.status === "pending";
    body = (
      <>
        <p className="text-sm font-semibold uppercase tracking-wide text-faint">Signature requested</p>
        <h1 className="mt-2 break-words text-3xl">{info.document_filename}</h1>
        <p className="mt-2 text-muted">
          {info.requested_by_name ? `${info.requested_by_name} asked` : "You've been asked"} you, {info.signer.name}, to sign this
          document{info.sent_at ? ` on ${formatDateTime(info.sent_at)}` : ""}.
        </p>
        {info.message && <p className="mt-3 whitespace-pre-wrap break-words rounded-lg border border-rule bg-page px-4 py-3">{info.message}</p>}

        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_22rem]">
          <div>{info.envelope_status !== "cancelled" && <Document token={token} filename={info.document_filename} />}</div>
          <div className="space-y-6">
            {canAct ? (
              <SignForm token={token} info={info} onDone={(res) => qc.setQueryData(["signing", token], res)} />
            ) : (
              <Outcome info={info} />
            )}
            <section>
              <h2 className="text-sm font-semibold text-muted">Signers</h2>
              <Progress signers={info.signers} closed={info.envelope_status !== "pending"} />
            </section>
            <p className="break-all text-xs text-faint">Document SHA-256: {info.document_sha256}</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6">
        <Logo href="/" />
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pb-16 pt-2 sm:px-6">{body}</main>
    </div>
  );
}
