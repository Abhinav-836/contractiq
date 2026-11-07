"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useActiveWorkspace, useCompleteObligation, useContracts, useObligations, useReopenObligation } from "@/lib/queries";
import { errorMessage } from "@/lib/api";
import { dueSortKey, formatDue } from "@/lib/format";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import { Empty, ErrorNote, Filters, Loading, PageHead } from "@/components/States";

const PRIORITY = { high: "High priority", medium: "Medium priority", low: "Low priority" };
const PRI_W = { high: 3, medium: 2, low: 1 };

export default function ObligationsPage() {
  const { data: all = [], isLoading, error, refetch } = useObligations();
  const { data: contracts = [] } = useContracts({ limit: 100 });
  const complete = useCompleteObligation();
  const reopen = useReopenObligation();
  const { canEdit } = useActiveWorkspace();
  const [filter, setFilter] = useState("open");
  const [sort, setSort] = useState("due");

  const names = useMemo(() => Object.fromEntries(contracts.map((c) => [c.id, c.filename])), [contracts]);

  const counts = {
    open: all.filter((o) => o.status !== "completed").length,
    overdue: all.filter((o) => o.status === "overdue").length,
    completed: all.filter((o) => o.status === "completed").length,
    all: all.length,
  };

  const shown = all
    .filter((o) => (filter === "all" ? true : filter === "open" ? o.status !== "completed" : o.status === filter))
    .slice()
    .sort((a, b) => {
      if (a.status === "overdue" && b.status !== "overdue") return -1;
      if (b.status === "overdue" && a.status !== "overdue") return 1;
      return sort === "priority"
        ? (PRI_W[b.priority] || 0) - (PRI_W[a.priority] || 0) || dueSortKey(a.due_date) - dueSortKey(b.due_date)
        : dueSortKey(a.due_date) - dueSortKey(b.due_date) || (PRI_W[b.priority] || 0) - (PRI_W[a.priority] || 0);
    });

  const toggle = (o) => {
    const done = o.status === "completed";
    (done ? reopen : complete).mutate(o.id, {
      onSuccess: () => {
        track(done ? "obligation_reopened" : "obligation_completed", { from: "list" });
        if (!done) toast("Marked as done.", "success");
      },
      onError: (err) => toast(errorMessage(err, "Couldn't update the obligation."), "error"),
    });
  };

  return (
    <div className="space-y-8">
      <PageHead
        title="Obligations"
        sub={
          isLoading
            ? "\u00a0"
            : counts.overdue
              ? `${counts.open} open, ${counts.overdue} overdue. Tick them off as you meet them.`
              : `${counts.open} open. Tick them off as you meet them.`
        }
      />

      {isLoading ? (
        <Loading label="Loading obligations…" />
      ) : error ? (
        <ErrorNote message={errorMessage(error, "Couldn't load obligations.")} onRetry={refetch} />
      ) : all.length === 0 ? (
        <Empty
          title="No obligations yet"
          body="When a contract is reviewed, the things it commits you to — payments, notices, deadlines — are listed here."
          action="Upload a contract"
          href="/contracts/upload"
        />
      ) : (
        <>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <Filters
              label="Show obligations"
              value={filter}
              onChange={setFilter}
              options={[
                ["open", "Open", counts.open],
                ...(counts.overdue ? [["overdue", "Overdue", counts.overdue]] : []),
                ["completed", "Done", counts.completed],
                ["all", "All", counts.all],
              ]}
            />
            <label className="flex shrink-0 items-center gap-2 whitespace-nowrap text-sm text-muted">
              Sort by
              <select value={sort} onChange={(e) => setSort(e.target.value)} className="field w-auto py-1.5">
                <option value="due">Due date</option>
                <option value="priority">Priority</option>
              </select>
            </label>
          </div>

          {shown.length === 0 ? (
            <p className="rounded-xl border border-dashed border-rule bg-page px-6 py-10 text-center text-muted">
              {filter === "open" ? "Everything's done. Nice." : "Nothing here."}
            </p>
          ) : (
            <ul className="divide-y divide-rule overflow-hidden rounded-xl border border-rule bg-page">
              {shown.map((o) => {
                const done = o.status === "completed";
                const due = formatDue(o.due_date);
                return (
                  <li key={o.id} className="flex gap-4 px-4 py-4 sm:px-5">
                    <input
                      type="checkbox"
                      checked={done}
                      disabled={!canEdit}
                      onChange={() => toggle(o)}
                      aria-label={`${done ? "Reopen" : "Mark done"}: ${o.description || o.title}`}
                      className="mt-1 h-[1.1rem] w-[1.1rem] shrink-0 accent-[var(--pen)]"
                    />
                    <div className="min-w-0 flex-1">
                      <p className={`max-w-[75ch] ${done ? "text-faint line-through" : ""}`}>{o.description || o.title}</p>
                      <p className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-faint">
                        {o.status === "overdue" ? (
                          <span className="font-semibold text-danger">Overdue{due ? `, ${due}` : ""}</span>
                        ) : (
                          <span>{due || "No date set"}</span>
                        )}
                        {o.priority && o.priority !== "medium" && <span>{PRIORITY[o.priority] || o.priority}</span>}
                        {o.assigned_to && <span>Assigned to {o.assigned_to}</span>}
                        {o.contract_id && (
                          <Link href={`/contracts/${o.contract_id}`} className="truncate text-pen hover:underline">
                            {names[o.contract_id] || "Source contract"}
                          </Link>
                        )}
                      </p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </>
      )}
    </div>
  );
}