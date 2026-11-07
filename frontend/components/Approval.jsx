"use client";

import { useEffect, useState } from "react";
import { approvalsAPI, errorMessage } from "@/lib/api";
import { formatDate, timeAgo } from "@/lib/format";
import { useActiveWorkspace, useApprovalMutation, useContractApprovals, useFeatures, useMembers } from "@/lib/queries";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import { ROLE_LABELS } from "@/lib/workspace";
import Modal from "./Modal";
import { Spinner } from "./States";

export const APPROVAL = {
  pending: { label: "Awaiting approval", tone: "bg-hi-med text-hi-med-ink" },
  approved: { label: "Approved", tone: "bg-hi-low text-hi-low-ink" },
  rejected: { label: "Rejected", tone: "bg-danger/10 text-danger" },
  cancelled: { label: "Cancelled", tone: "bg-bg text-muted" },
};

export function ApprovalBadge({ status, className = "" }) {
  const s = APPROVAL[status];
  if (!s) return null;
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-semibold ${s.tone} ${className}`}>{s.label}</span>;
}

const DECISION_MARK = {
  approved: { icon: "✓", label: "Approved", className: "text-ok" },
  rejected: { icon: "✕", label: "Rejected", className: "text-danger" },
};

/** One reviewer line: name, decision (or waiting), optional comment. */
function ReviewerRow({ r }) {
  const d = DECISION_MARK[r.decision];
  return (
    <li className="text-sm">
      <div className="flex items-baseline gap-2">
        <span aria-hidden="true" className={`w-3 shrink-0 font-semibold ${d ? d.className : "text-faint"}`}>
          {d ? d.icon : "•"}
        </span>
        <span className="min-w-0 flex-1 truncate">{r.name}</span>
        <span className={`shrink-0 ${d ? d.className : "text-faint"}`}>{d ? d.label : "Waiting"}</span>
      </div>
      {r.comment && <p className="ml-5 mt-1 whitespace-pre-wrap break-words text-muted">&ldquo;{r.comment}&rdquo;</p>}
    </li>
  );
}

/* ---------------- request modal ---------------- */
function RequestApproval({ open, onClose, contractId }) {
  const { active, userId } = useActiveWorkspace();
  const emailOn = Boolean(useFeatures().data?.email);
  const { data: members = [], isLoading } = useMembers(open ? active?.id : null);
  const [picked, setPicked] = useState([]);
  const [note, setNote] = useState("");
  const [error, setError] = useState("");
  const create = useApprovalMutation((body) => approvalsAPI.request(contractId, body));
  const candidates = members.filter((m) => m.user_id !== userId);

  useEffect(() => {
    if (open) {
      setPicked([]);
      setNote("");
      setError("");
    }
  }, [open]);

  const toggle = (id) => setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const submit = async (e) => {
    e.preventDefault();
    if (!picked.length) return setError("Pick at least one reviewer.");
    try {
      await create.mutateAsync({ reviewer_ids: picked, note: note.trim() || null });
      track("approval_requested", { reviewers: picked.length });
      toast(`Approval requested from ${picked.length} ${picked.length === 1 ? "person" : "people"}.`, "success");
      onClose();
    } catch (err) {
      setError(errorMessage(err, "Couldn't request approval."));
    }
  };

  return (
    <Modal open={open} onClose={() => !create.isPending && onClose()} title="Request approval">
      <form onSubmit={submit} noValidate>
        <p className="text-muted">
          Everyone you pick has to approve. One rejection sends it back to you.
          {emailOn && " Reviewers get an email, and you get one when it's decided."}
        </p>
        <fieldset className="mt-4">
          <legend className="mb-1.5 text-sm font-medium">Reviewers</legend>
          {isLoading ? (
            <p className="text-sm text-muted">Loading people…</p>
          ) : candidates.length === 0 ? (
            <p className="rounded-lg border border-rule bg-bg px-3 py-2.5 text-sm text-muted">
              Nobody else is in {active?.name || "this workspace"} yet. Invite someone from the Team page first.
            </p>
          ) : (
            <ul className="max-h-56 space-y-1 overflow-y-auto">
              {candidates.map((m) => (
                <li key={m.user_id}>
                  <label className="flex cursor-pointer items-center gap-3 rounded-md px-2 py-1.5 hover:bg-bg">
                    <input
                      type="checkbox"
                      checked={picked.includes(m.user_id)}
                      onChange={() => toggle(m.user_id)}
                      className="h-4 w-4 accent-[var(--pen)]"
                    />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium">{m.name}</span>
                      <span className="block truncate text-xs text-muted">
                        {ROLE_LABELS[m.role]} · {m.email}
                      </span>
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </fieldset>
        <label htmlFor="approval-note" className="mb-1.5 mt-4 block text-sm font-medium">
          Note <span className="font-normal text-faint">(optional)</span>
        </label>
        <textarea
          id="approval-note"
          className="field resize-y"
          rows={3}
          maxLength={2000}
          placeholder="What should they look at?"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />
        {error && (
          <p role="alert" className="mt-3 text-sm text-danger">
            {error}
          </p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" className="btn btn-quiet" onClick={onClose} disabled={create.isPending}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={create.isPending || !candidates.length}>
            {create.isPending && <Spinner />} Send request
          </button>
        </div>
      </form>
    </Modal>
  );
}

/* ---------------- decision ---------------- */
function DecisionForm({ request }) {
  const [rejecting, setRejecting] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const decide = useApprovalMutation(({ decision, comment: c }) => approvalsAPI.decide(request.id, decision, c));

  const send = async (decision) => {
    if (decision === "rejected" && !comment.trim()) return setError("Say why, so the requester knows what to change.");
    try {
      const res = await decide.mutateAsync({ decision, comment: comment.trim() || null });
      track("approval_decided", { decision });
      toast(
        decision === "rejected"
          ? "Rejected. The requester can see your reason."
          : res.status === "approved"
            ? "Approved. That was the last approval needed."
            : "Approved. Waiting for the other reviewers.",
        "success",
      );
    } catch (err) {
      setError(errorMessage(err, "Couldn't record your decision."));
    }
  };

  return (
    <div className="mt-4 rounded-lg border border-pen/40 bg-bg p-3">
      <p className="text-sm font-medium">Your approval is needed</p>
      <label htmlFor={`comment-${request.id}`} className="sr-only">
        Comment
      </label>
      <textarea
        id={`comment-${request.id}`}
        className="field mt-2 resize-y text-sm"
        rows={rejecting ? 3 : 2}
        maxLength={2000}
        placeholder={rejecting ? "Why are you rejecting it? (required)" : "Comment (optional)"}
        value={comment}
        aria-invalid={Boolean(error)}
        onChange={(e) => {
          setComment(e.target.value);
          setError("");
        }}
      />
      {error && <p className="mt-1.5 text-sm text-danger">{error}</p>}
      <div className="mt-2 flex gap-2">
        {rejecting ? (
          <>
            <button type="button" className="btn btn-danger flex-1 px-3 py-1.5" onClick={() => send("rejected")} disabled={decide.isPending}>
              {decide.isPending && <Spinner />} Reject
            </button>
            <button type="button" className="btn btn-quiet px-3 py-1.5" onClick={() => setRejecting(false)} disabled={decide.isPending}>
              Back
            </button>
          </>
        ) : (
          <>
            <button type="button" className="btn btn-primary flex-1 px-3 py-1.5" onClick={() => send("approved")} disabled={decide.isPending}>
              {decide.isPending && <Spinner />} Approve
            </button>
            <button type="button" className="btn btn-quiet px-3 py-1.5 text-danger" onClick={() => setRejecting(true)} disabled={decide.isPending}>
              Reject…
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* ---------------- panel on the contract page ---------------- */
export default function ApprovalPanel({ contractId, contractStatus }) {
  const { canEdit, canAdmin, userId } = useActiveWorkspace();
  const { data: requests = [], isLoading } = useContractApprovals(contractId);
  const [asking, setAsking] = useState(false);
  const cancel = useApprovalMutation((id) => approvalsAPI.cancel(id));
  const open = requests[0]?.status === "pending" ? requests[0] : null;
  const latestClosed = open ? null : requests.find((r) => r.status !== "cancelled") || null;
  const shown = open || latestClosed;
  const earlier = requests.filter((r) => r !== shown);

  const doCancel = async () => {
    try {
      await cancel.mutateAsync(open.id);
      toast("Approval request cancelled.");
    } catch (err) {
      toast(errorMessage(err, "Couldn't cancel the request."), "error");
    }
  };

  return (
    <section aria-labelledby="approval">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="approval" className="text-sm font-semibold text-muted">
          Approval
        </h2>
        {(open || latestClosed) && <ApprovalBadge status={open ? "pending" : latestClosed.status} />}
      </div>

      {isLoading ? (
        <p className="mt-2 text-sm text-muted">Loading…</p>
      ) : open ? (
        <div className="mt-3">
          <p className="text-sm text-muted">
            {open.requested_by === userId ? "You" : open.requested_by_name} asked {timeAgo(open.created_at)} ·{" "}
            {open.approved_count} of {open.reviewers.length} approved
          </p>
          {open.note && <p className="mt-2 whitespace-pre-wrap break-words rounded-md bg-bg px-3 py-2 text-sm">{open.note}</p>}
          <ul className="mt-3 space-y-2">
            {open.reviewers.map((r) => (
              <ReviewerRow key={r.user_id} r={r} />
            ))}
          </ul>
          {open.awaiting_my_decision && <DecisionForm request={open} />}
          {(open.requested_by === userId || canAdmin) && (
            <button
              type="button"
              className="mt-3 text-sm font-semibold text-muted underline-offset-4 hover:text-ink hover:underline"
              onClick={doCancel}
              disabled={cancel.isPending}
            >
              Cancel request
            </button>
          )}
        </div>
      ) : (
        <div className="mt-2">
          {latestClosed ? (
            <>
              <p className="text-sm text-muted">
                {latestClosed.status === "approved" ? "Approved" : "Rejected"} {formatDate(latestClosed.closed_at)}
                {latestClosed.closed_by_name ? ` (last decision by ${latestClosed.closed_by_name})` : ""}.
              </p>
              <ul className="mt-2 space-y-2">
                {latestClosed.reviewers.map((r) => (
                  <ReviewerRow key={r.user_id} r={r} />
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-muted">Nobody has been asked to approve this contract yet.</p>
          )}
          {canEdit && contractStatus === "completed" && (
            <button type="button" className="btn btn-quiet mt-3 w-full px-3 py-1.5" onClick={() => setAsking(true)}>
              {latestClosed ? "Request approval again" : "Request approval"}
            </button>
          )}
        </div>
      )}

      {earlier.length > 0 && (
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-muted hover:text-ink">Earlier requests</summary>
          <ul className="mt-2 space-y-2">
            {earlier.map((r) => (
              <li key={r.id} className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <ApprovalBadge status={r.status} />
                <span className="text-muted">
                  {formatDate(r.created_at)} · asked by {r.requested_by_name}
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}

      <RequestApproval open={asking} onClose={() => setAsking(false)} contractId={contractId} />
    </section>
  );
}
