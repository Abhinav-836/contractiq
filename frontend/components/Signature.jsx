"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { errorMessage, saveBlob, signaturesAPI, signingLink } from "@/lib/api";
import { formatDate, timeAgo } from "@/lib/format";
import { useActiveWorkspace, useContractSignatures, useEmailStatus, useMembers, useSignatureMutation } from "@/lib/queries";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import Modal from "./Modal";
import { Spinner } from "./States";

export const SIGNATURE = {
  pending: { label: "Out for signing", tone: "bg-hi-med text-hi-med-ink" },
  completed: { label: "Signed", tone: "bg-hi-low text-hi-low-ink" },
  declined: { label: "Signing declined", tone: "bg-danger/10 text-danger" },
  cancelled: { label: "Cancelled", tone: "bg-bg text-muted" },
};

export function SignatureBadge({ status, className = "" }) {
  const s = SIGNATURE[status];
  if (!s) return null;
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${s.tone} ${className}`}>{s.label}</span>;
}

const SIGNER_MARK = {
  signed: { icon: "✓", label: "Signed", className: "text-ok" },
  declined: { icon: "✕", label: "Declined", className: "text-danger" },
};

const EMAIL_NOTE = {
  sent: { text: "Emailed", className: "text-faint" },
  failed: { text: "Email failed — copy a new link instead", className: "text-danger" },
  skipped: { text: "Not emailed (daily email limit) — copy a new link instead", className: "text-danger" },
};

function SignerRow({ s, showEmail = false, children }) {
  const d = SIGNER_MARK[s.status];
  const note = showEmail && s.status === "pending" ? EMAIL_NOTE[s.email_status] : null;
  return (
    <li className="text-sm">
      <div className="flex items-baseline gap-2">
        <span aria-hidden="true" className={`w-3 shrink-0 font-semibold ${d ? d.className : "text-faint"}`}>
          {d ? d.icon : "•"}
        </span>
        <span className="min-w-0 flex-1 truncate" title={s.email}>
          {s.name}
        </span>
        <span className={`shrink-0 ${d ? d.className : "text-faint"}`}>
          {d ? d.label : s.viewed_at ? "Opened" : "Waiting"}
        </span>
      </div>
      {note && (
        <p className={`ml-5 mt-0.5 text-xs ${note.className}`} title={s.email_error || s.email}>
          {note.text}
        </p>
      )}
      {s.decline_reason && <p className="ml-5 mt-1 whitespace-pre-wrap break-words text-muted">&ldquo;{s.decline_reason}&rdquo;</p>}
      {children}
    </li>
  );
}

/* ---------------- signed PDF ---------------- */
export function DownloadSignedPdf({ envelope, className = "btn btn-quiet px-3 py-1.5", label = "Download signed PDF" }) {
  const [busy, setBusy] = useState(false);
  const download = async () => {
    setBusy(true);
    try {
      const res = await signaturesAPI.signedPdf(envelope.id);
      const base = envelope.document_filename.replace(/\.[^.]+$/, "");
      saveBlob(res, `${base} (signed).pdf`);
      track("signed_pdf_downloaded");
    } catch (err) {
      // Errors come back as a Blob because of responseType: "blob".
      let msg = "Couldn't make the signed PDF.";
      try {
        msg = JSON.parse(await err.response.data.text()).detail || msg;
      } catch {
        msg = errorMessage(err, msg);
      }
      toast(msg, "error");
    } finally {
      setBusy(false);
    }
  };
  return (
    <button type="button" className={className} onClick={download} disabled={busy}>
      {busy && <Spinner />} {busy ? "Preparing PDF…" : label}
    </button>
  );
}

/* ---------------- links, shown once ---------------- */
function CopyButton({ text, label = "Copy link" }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setDone(true);
      setTimeout(() => setDone(false), 1800);
    } catch {
      toast("Couldn't copy. Select the link and copy it yourself.", "error");
    }
  };
  return (
    <button type="button" className="btn btn-quiet shrink-0 px-3 py-1.5 text-sm" onClick={copy}>
      {done ? "Copied" : label}
    </button>
  );
}

function mailto(signer, url, envelope) {
  const subject = `Please sign: ${envelope.document_filename}`;
  const body = [
    `Hi ${signer.name},`,
    "",
    `${envelope.requested_by_name} has asked you to sign "${envelope.document_filename}".`,
    envelope.message ? `\n${envelope.message}\n` : "",
    "Open this private link to read and sign it (no account needed):",
    url,
    "",
    "This link is just for you, so please don't forward it.",
  ].join("\n");
  return `mailto:${encodeURIComponent(signer.email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

export function LinksModal({ envelope, onClose }) {
  const links = envelope?.links || {};
  const signers = (envelope?.signers || []).filter((s) => links[s.id]);
  const emailed = Boolean(envelope?.emailed);
  const many = signers.length > 1;
  const title = emailed
    ? many ? "Signing links emailed" : "Signing link emailed"
    : many ? "Send each person their link" : "Send the signing link";
  return (
    <Modal open={Boolean(envelope)} onClose={onClose} title={title}>
      {emailed ? (
        <p className="text-muted">
          We&apos;re emailing {many ? "each person their own link" : `${signers[0]?.name} their link`} now. You&apos;ll see
          &ldquo;Emailed&rdquo; next to each name once it&apos;s gone. Copies are below in case you also want to share them
          another way — <strong className="font-semibold text-ink">this is the only time they&apos;re shown</strong>.
        </p>
      ) : (
        <p className="text-muted">
          Share each link yourself — each one is private to that person.{" "}
          <strong className="font-semibold text-ink">This is the only time the links are shown</strong> — if one gets lost,
          make a new one.
        </p>
      )}
      <ul className="mt-4 max-h-72 space-y-3 overflow-y-auto">
        {signers.map((s) => {
          const url = signingLink(links[s.id]);
          return (
            <li key={s.id} className="rounded-lg border border-rule p-3">
              <p className="text-sm font-medium">
                {s.name} <span className="font-normal text-muted">· {s.email}</span>
              </p>
              <input
                readOnly
                value={url}
                aria-label={`Signing link for ${s.name}`}
                onFocus={(e) => e.target.select()}
                className="field mt-2 font-mono text-xs"
              />
              <div className="mt-2 flex gap-2">
                <CopyButton text={url} />
                <a className="btn btn-quiet px-3 py-1.5 text-sm" href={mailto(s, url, envelope)}>
                  Email it
                </a>
              </div>
            </li>
          );
        })}
      </ul>
      <div className="mt-6 flex justify-end">
        <button type="button" className="btn btn-primary" onClick={onClose}>
          Done
        </button>
      </div>
    </Modal>
  );
}

/* ---------------- send-for-signing modal ---------------- */
const blank = () => ({ name: "", email: "" });
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function SendForSigning({ open, onClose, contractId, approvalStatus, onSent }) {
  const { active } = useActiveWorkspace();
  const { emailOn: serverEmail, verified } = useEmailStatus();
  const emailOn = serverEmail && verified; // can't email signers until your own address is confirmed
  const [sendEmail, setSendEmail] = useState(true);
  const { data: members = [] } = useMembers(open ? active?.id : null);
  const [rows, setRows] = useState([blank()]);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const send = useSignatureMutation((body) => signaturesAPI.send(contractId, body));

  useEffect(() => {
    if (open) {
      setRows([blank()]);
      setMessage("");
      setError("");
      setSendEmail(true);
    }
  }, [open]);

  const used = new Set(rows.map((r) => r.email.trim().toLowerCase()).filter(Boolean));
  const teammates = members.filter((m) => !used.has(m.email.toLowerCase()));

  const setRow = (i, key, value) => {
    setRows((rs) => rs.map((r, j) => (j === i ? { ...r, [key]: value } : r)));
    setError("");
  };
  const addTeammate = (m) =>
    setRows((rs) => {
      const person = { name: m.name, email: m.email };
      const emptyAt = rs.findIndex((r) => !r.name.trim() && !r.email.trim());
      return emptyAt >= 0 ? rs.map((r, j) => (j === emptyAt ? person : r)) : [...rs, person].slice(0, 10);
    });

  const submit = async (e) => {
    e.preventDefault();
    const signers = rows
      .map((r) => ({ name: r.name.trim().replace(/\s+/g, " "), email: r.email.trim() }))
      .filter((r) => r.name || r.email);
    if (!signers.length) return setError("Add at least one person to sign.");
    const bad = signers.find((r) => !r.name || !EMAIL.test(r.email));
    if (bad) return setError(bad.name ? `Check the email for ${bad.name}.` : "Every signer needs a full name.");
    const emails = signers.map((r) => r.email.toLowerCase());
    if (new Set(emails).size !== emails.length) return setError("The same email is listed twice.");
    try {
      const env = await send.mutateAsync({ signers, message: message.trim() || null, send_email: emailOn && sendEmail });
      track("signature_requested", { signers: signers.length, emailed: Boolean(env.emailed) });
      onClose();
      onSent(env);
    } catch (err) {
      setError(errorMessage(err, "Couldn't send for signing."));
    }
  };

  return (
    <Modal open={open} onClose={() => !send.isPending && onClose()} title="Send for signing">
      <form onSubmit={submit} noValidate>
        <p className="text-muted">
          Each person gets a private link{emailOn ? " by email" : ""}. They read the contract, type their name and agree — no
          account needed. Everyone has to sign.
        </p>
        {approvalStatus !== "approved" && (
          <p className="mt-3 rounded-lg border border-rule bg-hi-med/40 px-3 py-2 text-sm">
            {approvalStatus === "pending"
              ? "Heads up: this contract is still waiting for approval."
              : approvalStatus === "rejected"
                ? "Heads up: the last approval request for this contract was rejected."
                : "Heads up: nobody has approved this contract yet."}
          </p>
        )}

        <fieldset className="mt-4">
          <legend className="mb-1.5 text-sm font-medium">Who needs to sign</legend>
          <ul className="space-y-2">
            {rows.map((r, i) => (
              <li key={i} className="flex items-start gap-2">
                <div className="grid min-w-0 flex-1 gap-2 sm:grid-cols-2">
                  <input
                    className="field text-sm"
                    placeholder="Full name"
                    aria-label={`Signer ${i + 1} full name`}
                    maxLength={120}
                    value={r.name}
                    onChange={(e) => setRow(i, "name", e.target.value)}
                  />
                  <input
                    className="field text-sm"
                    type="email"
                    placeholder="Email"
                    aria-label={`Signer ${i + 1} email`}
                    value={r.email}
                    onChange={(e) => setRow(i, "email", e.target.value)}
                  />
                </div>
                {rows.length > 1 && (
                  <button
                    type="button"
                    className="mt-2 shrink-0 px-1 text-faint hover:text-danger"
                    aria-label={`Remove signer ${i + 1}`}
                    onClick={() => setRows((rs) => rs.filter((_, j) => j !== i))}
                  >
                    ✕
                  </button>
                )}
              </li>
            ))}
          </ul>
          {rows.length < 10 && (
            <button
              type="button"
              className="mt-2 text-sm font-semibold text-pen underline-offset-4 hover:underline"
              onClick={() => setRows((rs) => [...rs, blank()])}
            >
              + Add another person
            </button>
          )}
          {teammates.length > 0 && rows.length <= 10 && (
            <div className="mt-3">
              <p className="text-xs text-muted">Or add someone from {active?.name || "your workspace"}:</p>
              <div className="mt-1.5 flex flex-wrap gap-1.5">
                {teammates.slice(0, 8).map((m) => (
                  <button
                    key={m.user_id}
                    type="button"
                    className="rounded-full border border-rule px-2.5 py-1 text-xs hover:border-pen hover:text-pen"
                    onClick={() => addTeammate(m)}
                  >
                    + {m.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </fieldset>

        <label htmlFor="sign-message" className="mb-1.5 mt-4 block text-sm font-medium">
          Message <span className="font-normal text-faint">(optional, shown to signers)</span>
        </label>
        <textarea
          id="sign-message"
          className="field resize-y"
          rows={2}
          maxLength={2000}
          placeholder="e.g. Please sign by Friday."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />
        {serverEmail && !verified && (
          <p className="mt-4 rounded-md bg-bg px-3 py-2 text-sm text-muted">
            Confirm your email address (see the banner at the top) to have ContractIQ email the links. For now you&apos;ll get the
            links to share yourself.
          </p>
        )}
        {emailOn && (
          <label className="mt-4 flex cursor-pointer items-start gap-3 text-sm">
            <input
              type="checkbox"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
              className="mt-0.5 h-4 w-4 shrink-0 accent-[var(--pen)]"
            />
            <span>
              Email each person their link
              <span className="block text-xs text-faint">Untick to copy and share the links yourself.</span>
            </span>
          </label>
        )}
        {error && (
          <p role="alert" className="mt-3 text-sm text-danger">
            {error}
          </p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" className="btn btn-quiet" onClick={onClose} disabled={send.isPending}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={send.isPending}>
            {send.isPending && <Spinner />} {emailOn && sendEmail ? "Send for signing" : "Create signing links"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

/* ---------------- panel on the contract page ---------------- */
export default function SignaturePanel({ contractId, contractStatus, approvalStatus }) {
  const { canEdit } = useActiveWorkspace();
  const { data: envelopes = [], isLoading } = useContractSignatures(contractId);
  const [sending, setSending] = useState(false);
  const [links, setLinks] = useState(null);
  const cancel = useSignatureMutation((id) => signaturesAPI.cancel(id));
  const reissue = useSignatureMutation(({ id, signerId }) => signaturesAPI.newLink(id, signerId));
  const remind = useSignatureMutation(({ id, signerId }) => signaturesAPI.remind(id, signerId));
  const { emailOn: serverEmail, verified } = useEmailStatus();
  const emailOn = serverEmail && verified;

  const open = envelopes[0]?.status === "pending" ? envelopes[0] : null;
  const latestClosed = open ? null : envelopes.find((e) => e.status !== "cancelled") || null;
  const shown = open || latestClosed;
  const earlier = envelopes.filter((e) => e !== shown);

  const doCancel = async () => {
    try {
      await cancel.mutateAsync(open.id);
      toast("Signing cancelled. The links no longer work.");
    } catch (err) {
      toast(errorMessage(err, "Couldn't cancel."), "error");
    }
  };
  const newLink = async (signer) => {
    try {
      const env = await reissue.mutateAsync({ id: open.id, signerId: signer.id });
      track("signature_link_reissued");
      setLinks(env);
    } catch (err) {
      toast(errorMessage(err, "Couldn't make a new link."), "error");
    }
  };
  const sendReminder = async (signer) => {
    try {
      await remind.mutateAsync({ id: open.id, signerId: signer.id });
      track("signature_reminder_sent");
      toast(`Reminder emailed to ${signer.name} with a fresh link.`, "success");
    } catch (err) {
      toast(errorMessage(err, "Couldn't send the reminder."), "error");
    }
  };

  return (
    <section aria-labelledby="signatures">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="signatures" className="text-sm font-semibold text-muted">
          Signatures
        </h2>
        {shown && <SignatureBadge status={shown.status} />}
      </div>

      {isLoading ? (
        <p className="mt-2 text-sm text-muted">Loading…</p>
      ) : open ? (
        <div className="mt-3">
          <p className="text-sm text-muted">
            Sent by {open.requested_by_name} {timeAgo(open.created_at)} · {open.signed_count} of {open.signers.length} signed
          </p>
          <ul className="mt-3 space-y-2">
            {open.signers.map((s) => (
              <SignerRow key={s.id} s={s} showEmail>
                {open.can_manage && s.status === "pending" && (
                  <div className="ml-5 mt-0.5 flex flex-wrap gap-x-3">
                    {emailOn && (
                      <button
                        type="button"
                        className="text-xs font-semibold text-pen underline-offset-4 hover:underline"
                        onClick={() => sendReminder(s)}
                        disabled={remind.isPending}
                        title="Email a fresh link as a reminder (at most once an hour)"
                      >
                        Email reminder
                      </button>
                    )}
                    <button
                      type="button"
                      className="text-xs font-semibold text-muted underline-offset-4 hover:text-ink hover:underline"
                      onClick={() => newLink(s)}
                      disabled={reissue.isPending}
                    >
                      New link
                    </button>
                  </div>
                )}
              </SignerRow>
            ))}
          </ul>
          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1">
            <Link href={`/signatures/${open.id}`} className="text-sm font-semibold text-pen underline-offset-4 hover:underline">
              Audit trail
            </Link>
            {open.can_manage && (
              <button
                type="button"
                className="text-sm font-semibold text-muted underline-offset-4 hover:text-ink hover:underline"
                onClick={doCancel}
                disabled={cancel.isPending}
              >
                Cancel signing
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="mt-2">
          {latestClosed ? (
            <>
              <p className="text-sm text-muted">
                {latestClosed.status === "completed" ? "Everyone signed" : "Declined"} {formatDate(latestClosed.closed_at)}.
              </p>
              <ul className="mt-2 space-y-2">
                {latestClosed.signers.map((s) => (
                  <SignerRow key={s.id} s={s} />
                ))}
              </ul>
              <Link
                href={`/signatures/${latestClosed.id}`}
                className="mt-3 inline-block text-sm font-semibold text-pen underline-offset-4 hover:underline"
              >
                {latestClosed.status === "completed" ? "View signature certificate" : "View audit trail"}
              </Link>
              {latestClosed.status === "completed" && (
                <DownloadSignedPdf envelope={latestClosed} className="btn btn-primary mt-3 w-full px-3 py-1.5" />
              )}
            </>
          ) : (
            <p className="text-sm text-muted">Not sent for signing yet.</p>
          )}
          {canEdit && contractStatus === "completed" && (
            <button type="button" className="btn btn-quiet mt-3 w-full px-3 py-1.5" onClick={() => setSending(true)}>
              {latestClosed ? "Send for signing again" : "Send for signing"}
            </button>
          )}
        </div>
      )}

      {earlier.length > 0 && (
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-muted hover:text-ink">Earlier requests</summary>
          <ul className="mt-2 space-y-2">
            {earlier.map((e) => (
              <li key={e.id} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <SignatureBadge status={e.status} />
                <Link href={`/signatures/${e.id}`} className="text-muted hover:text-ink hover:underline">
                  {formatDate(e.created_at)} · {e.requested_by_name}
                </Link>
              </li>
            ))}
          </ul>
        </details>
      )}

      <SendForSigning
        open={sending}
        onClose={() => setSending(false)}
        contractId={contractId}
        approvalStatus={approvalStatus}
        onSent={setLinks}
      />
      <LinksModal envelope={links} onClose={() => setLinks(null)} />
    </section>
  );
}
