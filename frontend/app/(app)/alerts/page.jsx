"use client";

import { useState } from "react";
import Link from "next/link";
import { useActiveWorkspace, useAlerts, useAlertStats, useDismissAlert, useMarkAlertRead, useMarkAllAlertsRead } from "@/lib/queries";
import { errorMessage } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { toast } from "@/lib/toast";
import { Empty, ErrorNote, Filters, Loading, PageHead } from "@/components/States";

const TYPE = {
  risk: { label: "Risk", mark: "bg-mark-high" },
  expiry: { label: "Expiry", mark: "bg-mark-med" },
  renewal: { label: "Renewal", mark: "bg-mark-med" },
  obligation: { label: "Obligation", mark: "bg-pen" },
};

export default function AlertsPage() {
  const [filter, setFilter] = useState("all");
  const { data: alerts = [], isLoading, error, refetch } = useAlerts();
  const { data: stats } = useAlertStats();
  const markRead = useMarkAlertRead();
  const markAll = useMarkAllAlertsRead();
  const dismiss = useDismissAlert();
  const { canEdit } = useActiveWorkspace();

  const unread = stats?.unread ?? alerts.filter((a) => !a.read).length;
  const types = [...new Set(alerts.map((a) => a.type).filter(Boolean))];
  const shown = alerts.filter((a) => (filter === "all" ? true : filter === "unread" ? !a.read : a.type === filter));

  const onError = (fallback) => (err) => toast(errorMessage(err, fallback), "error");

  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <PageHead title="Alerts" sub={isLoading ? "\u00a0" : unread ? `${unread} unread` : "You're all caught up."}>
        {canEdit && unread > 0 && (
          <button
            type="button"
            className="btn btn-quiet"
            disabled={markAll.isPending}
            onClick={() => markAll.mutate(undefined, { onSuccess: () => toast("All alerts marked as read.", "success"), onError: onError("Couldn't update alerts.") })}
          >
            Mark all as read
          </button>
        )}
      </PageHead>

      {isLoading ? (
        <Loading label="Loading alerts…" />
      ) : error ? (
        <ErrorNote message={errorMessage(error, "Couldn't load alerts.")} onRetry={refetch} />
      ) : alerts.length === 0 ? (
        <Empty title="No alerts" body="High-risk clauses, renewals and approaching deadlines from your contracts will show up here." />
      ) : (
        <>
          <Filters
            label="Show alerts"
            value={filter}
            onChange={setFilter}
            options={[
              ["all", "All", alerts.length],
              ["unread", "Unread", alerts.filter((a) => !a.read).length],
              ...types.map((t) => [t, TYPE[t]?.label || t, alerts.filter((a) => a.type === t).length]),
            ]}
          />
          {shown.length === 0 ? (
            <p className="rounded-xl border border-dashed border-rule bg-page px-6 py-10 text-center text-muted">Nothing here.</p>
          ) : (
            <ul className="divide-y divide-rule overflow-hidden rounded-xl border border-rule bg-page">
              {shown.map((a) => {
                const t = TYPE[a.type] || { label: a.type || "Alert", mark: "bg-faint" };
                return (
                  <li key={a.id} className={`flex gap-4 px-4 py-4 sm:px-5 ${a.read ? "" : "bg-pen/[0.03]"}`}>
                    <span aria-hidden="true" className={`mt-2 h-2 w-2 shrink-0 rounded-full ${a.read ? "bg-transparent ring-1 ring-rule" : t.mark}`} />
                    <div className="min-w-0 flex-1">
                      <p className={a.read ? "text-muted" : "font-semibold"}>
                        {a.title}
                        {!a.read && <span className="sr-only"> (unread)</span>}
                      </p>
                      <p className="mt-0.5 max-w-[70ch] text-muted">{a.message}</p>
                      <p className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-faint">
                        <span>
                          {t.label}, {formatDateTime(a.created_at)}
                        </span>
                        {a.contract_id && (
                          <Link
                            href={`/contracts/${a.contract_id}`}
                            onClick={() => canEdit && !a.read && markRead.mutate(a.id)}
                            className="text-pen hover:underline"
                          >
                            Open contract
                          </Link>
                        )}
                        {canEdit && !a.read && (
                          <button type="button" className="hover:text-ink" onClick={() => markRead.mutate(a.id, { onError: onError("Couldn't update the alert.") })}>
                            Mark as read
                          </button>
                        )}
                      </p>
                    </div>
                    {canEdit && <button
                      type="button"
                      aria-label={`Dismiss: ${a.title}`}
                      onClick={() => dismiss.mutate(a.id, { onError: onError("Couldn't dismiss the alert.") })}
                      className="h-8 shrink-0 rounded-md px-2 text-sm text-faint hover:bg-bg hover:text-ink"
                    >
                      Dismiss
                    </button>}
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