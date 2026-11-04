"use client";

import Link from "next/link";
import { useAlerts, useAlertStats, useContracts, useContractStats, useObligations, useObligationStats } from "@/lib/queries";
import { useSession } from "@/lib/session";
import { formatDue, dueSortKey } from "@/lib/format";
import ContractTable from "@/components/ContractTable";
import { Empty, ErrorNote, Loading } from "@/components/States";

function Figure({ value, label, href, tone }) {
  return (
    <Link href={href} className="group block rounded-lg px-1 py-2">
      <dd className={`font-serif text-4xl font-semibold tabular-nums ${tone || ""}`}>{value ?? "—"}</dd>
      <dt className="mt-1 text-sm text-muted group-hover:text-ink">{label}</dt>
    </Link>
  );
}

const greeting = () => {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
};

export default function Dashboard() {
  const session = useSession();
  const contracts = useContracts({ limit: 6 });
  const cStats = useContractStats();
  const oStats = useObligationStats();
  const aStats = useAlertStats();
  const open = useObligations({ status: "pending" });
  const overdue = useObligations({ status: "overdue" });
  const alerts = useAlerts({ unread_only: true });

  const first = session?.user?.name?.split(" ")[0];
  const due = [...(overdue.data || []), ...(open.data || [])]
    .sort((a, b) => (a.status === "overdue" ? -1 : 0) - (b.status === "overdue" ? -1 : 0) || dueSortKey(a.due_date) - dueSortKey(b.due_date))
    .slice(0, 5);
  const highRisk = cStats.data?.high_risk ?? 0;

  return (
    <div className="space-y-12">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-3xl sm:text-4xl">
            {greeting()}
            {first ? `, ${first}` : ""}.
          </h1>
          <p className="mt-2 text-muted">
            {cStats.data
              ? cStats.data.total_contracts === 0
                ? "Upload a contract to get its first review."
                : highRisk > 0
                  ? `${highRisk} of your contracts ${highRisk === 1 ? "has" : "have"} high-risk terms to look at.`
                  : "None of your contracts are high risk right now."
              : "\u00a0"}
          </p>
        </div>
        <Link href="/contracts/upload" className="btn btn-primary self-start sm:self-auto">
          Upload contract
        </Link>
      </div>

      <dl className="grid grid-cols-2 gap-x-6 gap-y-4 border-y border-rule py-5 sm:grid-cols-4">
        <Figure value={cStats.data?.total_contracts} label="Contracts" href="/contracts" />
        <Figure value={cStats.data ? highRisk : undefined} label="High risk" href="/contracts?risk=high" tone={highRisk ? "text-mark-high" : ""} />
        <Figure
          value={oStats.data ? (oStats.data.pending ?? 0) + (oStats.data.overdue ?? 0) : undefined}
          label={oStats.data?.overdue ? `Open obligations, ${oStats.data.overdue} overdue` : "Open obligations"}
          href="/obligations"
        />
        <Figure value={aStats.data?.unread} label="Unread alerts" href="/alerts" />
      </dl>

      <div className="grid gap-12 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <section aria-labelledby="recent">
          <div className="flex items-baseline justify-between">
            <h2 id="recent" className="text-xl">
              Recent contracts
            </h2>
            <Link href="/contracts" className="text-sm text-pen hover:underline">
              All contracts
            </Link>
          </div>
          <div className="mt-4">
            {contracts.isLoading ? (
              <Loading />
            ) : contracts.error ? (
              <ErrorNote message="Couldn't load your contracts." onRetry={() => contracts.refetch()} />
            ) : contracts.data.length === 0 ? (
              <Empty title="No contracts yet" body="Upload a PDF, Word or text contract and the review appears in about a minute." action="Upload a contract" href="/contracts/upload" />
            ) : (
              <ContractTable contracts={contracts.data} />
            )}
          </div>
        </section>

        <div className="space-y-10">
          <section aria-labelledby="due">
            <div className="flex items-baseline justify-between">
              <h2 id="due" className="text-xl">
                Coming due
              </h2>
              <Link href="/obligations" className="text-sm text-pen hover:underline">
                All obligations
              </Link>
            </div>
            {open.isLoading ? (
              <Loading />
            ) : due.length === 0 ? (
              <p className="mt-4 text-muted">Nothing open. Obligations from your contracts show up here.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {due.map((o) => (
                  <li key={o.id} className="border-l-2 border-rule pl-3">
                    <p className="line-clamp-2 text-sm">{o.description || o.title}</p>
                    <p className={`mt-0.5 text-sm ${o.status === "overdue" ? "font-semibold text-danger" : "text-faint"}`}>
                      {o.status === "overdue" ? "Overdue" : formatDue(o.due_date) || "No date set"}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section aria-labelledby="alerts-h">
            <div className="flex items-baseline justify-between">
              <h2 id="alerts-h" className="text-xl">
                Unread alerts
              </h2>
              <Link href="/alerts" className="text-sm text-pen hover:underline">
                All alerts
              </Link>
            </div>
            {alerts.isLoading ? (
              <Loading />
            ) : !alerts.data?.length ? (
              <p className="mt-4 text-muted">You&rsquo;re all caught up.</p>
            ) : (
              <ul className="mt-4 space-y-3">
                {alerts.data.slice(0, 4).map((a) => (
                  <li key={a.id}>
                    <Link href={a.contract_id ? `/contracts/${a.contract_id}` : "/alerts"} className="block text-sm hover:text-pen">
                      <span className="font-medium">{a.title}</span>
                      <span className="mt-0.5 line-clamp-2 block text-muted">{a.message}</span>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}