"use client";

import { useState } from "react";
import Link from "next/link";
import { errorMessage } from "@/lib/api";
import { timeAgo } from "@/lib/format";
import { useActiveWorkspace, useApprovals, useApprovalStats } from "@/lib/queries";
import { ApprovalBadge } from "@/components/Approval";
import { Empty, ErrorNote, Filters, Loading, PageHead } from "@/components/States";

const VIEWS = {
  waiting: { params: { scope: "waiting" }, empty: ["Nothing waiting for you", "When someone asks you to approve a contract, it shows up here."] },
  requested: { params: { scope: "requested" }, empty: ["You haven't asked for any approvals", "Open a reviewed contract and use Request approval in the sidebar."] },
  pending: { params: { scope: "all", status: "pending" }, empty: ["No open requests", "Nothing in this workspace is waiting for approval."] },
  all: { params: { scope: "all" }, empty: ["No approvals yet", "Approval requests in this workspace will be listed here."] },
};

function Reviewers({ request }) {
  const waiting = request.reviewers.filter((r) => !r.decision).map((r) => r.name);
  const rejected = request.reviewers.find((r) => r.decision === "rejected");
  if (request.status === "rejected" && rejected) return <span>Rejected by {rejected.name}</span>;
  if (request.status === "pending") {
    return (
      <span>
        {request.approved_count} of {request.reviewers.length} approved{waiting.length ? ` · waiting for ${waiting.join(", ")}` : ""}
      </span>
    );
  }
  return <span>{request.reviewers.map((r) => r.name).join(", ")}</span>;
}

export default function ApprovalsPage() {
  const [view, setView] = useState("waiting");
  const { active } = useActiveWorkspace();
  const { data: stats } = useApprovalStats();
  const { data: requests = [], isLoading, error, refetch } = useApprovals(VIEWS[view].params);

  const options = [
    ["waiting", "Waiting for me", stats?.waiting_for_me],
    ["requested", "Requested by me"],
    ["pending", "All open", stats?.pending],
    ["all", "Everything"],
  ];

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <PageHead
        title="Approvals"
        sub={
          stats
            ? stats.waiting_for_me
              ? `${stats.waiting_for_me} contract${stats.waiting_for_me === 1 ? "" : "s"} waiting for your decision in ${active?.name || "this workspace"}.`
              : `Nothing is waiting for you in ${active?.name || "this workspace"}.`
            : " "
        }
      />
      <Filters label="Show" value={view} onChange={setView} options={options} />

      {isLoading ? (
        <Loading label="Loading approvals…" />
      ) : error ? (
        <ErrorNote message={errorMessage(error, "Couldn't load approvals.")} onRetry={refetch} />
      ) : requests.length === 0 ? (
        <Empty title={VIEWS[view].empty[0]} body={VIEWS[view].empty[1]} />
      ) : (
        <ul className="divide-y divide-rule overflow-hidden rounded-xl border border-rule bg-page">
          {requests.map((r) => (
            <li key={r.id} className="relative px-4 py-4 hover:bg-bg/60 sm:px-5">
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                <Link
                  href={`/contracts/${r.contract_id}`}
                  className="min-w-0 truncate font-medium after:absolute after:inset-0 hover:text-pen"
                >
                  {r.contract_filename || "Contract"}
                </Link>
                <ApprovalBadge status={r.status} />
                {r.awaiting_my_decision && (
                  <span className="ml-auto rounded-full bg-pen px-2 py-0.5 text-xs font-semibold text-pen-ink">Your turn</span>
                )}
              </div>
              <p className="mt-1 text-sm text-faint">
                Asked by {r.requested_by_name} {timeAgo(r.created_at)} · <Reviewers request={r} />
              </p>
              {r.note && <p className="mt-2 line-clamp-2 max-w-[70ch] text-sm text-muted">{r.note}</p>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
