"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useActiveWorkspace, useAnalysis, useCompleteObligation, useContract, useDeleteContract, useInvalidateAll, useObligations, useReanalyze } from "@/lib/queries";
import { errorMessage } from "@/lib/api";
import { fileKind, fileSize, formatDate, formatDue } from "@/lib/format";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import ClauseReview, { orderClauses } from "@/components/ClauseReview";
import RiskBar from "@/components/RiskBar";
import { ConfirmDelete } from "@/components/Modal";
import ApprovalPanel from "@/components/Approval";
import { RiskMeter } from "@/components/Risk";
import { ErrorNote, Filters, Loading, Spinner } from "@/components/States";

function Reviewing() {
  return (
    <div className="mt-8 overflow-hidden rounded-xl border border-rule bg-page p-8" role="status">
      <div className="relative mx-auto h-24 w-20 rounded-sm border border-rule bg-bg">
        <div className="absolute inset-x-3 top-3 space-y-2">
          {[90, 70, 85, 60, 80].map((w, i) => (
            <div key={i} className="h-1 rounded bg-rule" style={{ width: `${w}%` }} />
          ))}
        </div>
        <div className="scan-line absolute inset-x-0 top-0 h-1/2">
          <div className="absolute bottom-0 h-0.5 w-full bg-pen/70" />
        </div>
      </div>
      <h2 className="mt-6 text-center text-xl">Reading the contract</h2>
      <p className="mx-auto mt-2 max-w-[44ch] text-center text-muted">
        Finding clauses, scoring each one and pulling out obligations. This page updates by itself when it&rsquo;s done.
      </p>
    </div>
  );
}

function Failed({ onRetry, busy, canEdit = true }) {
  return (
    <div className="mt-8 rounded-xl border border-rule bg-page p-8">
      <h2 className="text-xl">The review didn&rsquo;t finish</h2>
      <p className="mt-2 max-w-[60ch] text-muted">
        Either no readable text was found or the review was interrupted. If it fails again, the file may be password-protected, damaged,
        or a scan with no text layer.
      </p>
      {canEdit && <div className="mt-5 flex flex-wrap gap-2">
        <button type="button" className="btn btn-primary" onClick={onRetry} disabled={busy}>
          {busy && <Spinner />} {busy ? "Restarting…" : "Review it again"}
        </button>
        <Link href="/contracts/upload" className="btn btn-quiet">
          Upload a different file
        </Link>
      </div>}
    </div>
  );
}

function ContractObligations({ contractId, canEdit }) {
  const { data = [], isLoading } = useObligations({ contract_id: contractId });
  const complete = useCompleteObligation();
  if (isLoading) return <Loading />;
  if (!data.length) return <p className="text-sm text-muted">No obligations were found in this contract.</p>;
  return (
    <ul className="space-y-3">
      {data.map((o) => {
        const done = o.status === "completed";
        return (
          <li key={o.id} className="flex gap-3">
            <input
              type="checkbox"
              checked={done}
              disabled={done || complete.isPending || !canEdit}
              onChange={() =>
                complete.mutate(o.id, {
                  onSuccess: () => track("obligation_completed", { from: "contract" }),
                  onError: (err) => toast(errorMessage(err, "Couldn't update the obligation."), "error"),
                })
              }
              aria-label={`Mark done: ${o.description || o.title}`}
              className="mt-1 h-4 w-4 shrink-0 accent-[var(--pen)]"
            />
            <div className="min-w-0 text-sm">
              <p className={done ? "text-faint line-through" : ""}>{o.description || o.title}</p>
              <p className={`mt-0.5 ${o.status === "overdue" ? "font-semibold text-danger" : "text-faint"}`}>
                {o.status === "overdue" ? "Overdue" : done ? "Done" : formatDue(o.due_date) || "No date set"}
              </p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}

export default function ContractPage() {
  const { id } = useParams();
  const router = useRouter();
  const contract = useContract(id);
  const c = contract.data;
  const analysis = useAnalysis(id, c?.status === "completed");
  const a = analysis.data;
  const del = useDeleteContract();
  const reanalyze = useReanalyze();
  const { canEdit, canAdmin, userId } = useActiveWorkspace();
  const invalidateAll = useInvalidateAll();
  const [confirm, setConfirm] = useState(false);
  const [filter, setFilter] = useState("all");

  // When a review finishes, new obligations and alerts exist — refresh those views.
  const prev = useRef(c?.status);
  useEffect(() => {
    if (prev.current === "processing" && c?.status && c.status !== "processing") invalidateAll();
    prev.current = c?.status;
  }, [c?.status]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (c?.filename) document.title = `${c.filename} · ContractIQ`;
  }, [c?.filename]);

  if (contract.isLoading) return <Loading label="Opening the contract…" />;

  if (contract.error) {
    if (contract.error?.response?.status === 404) {
      return (
        <div className="mx-auto max-w-xl py-10">
          <h1 className="text-3xl">This contract isn&rsquo;t here</h1>
          <p className="mt-3 text-muted">It may have been deleted, or it belongs to another account.</p>
          <Link href="/contracts" className="btn btn-primary mt-6">
            Go to your contracts
          </Link>
        </div>
      );
    }
    return <ErrorNote message={errorMessage(contract.error, "Couldn't open this contract.")} onRetry={() => contract.refetch()} />;
  }

  const notContract = a?.risk_level === "not_contract";
  const clauses = a?.clauses || [];
  const count = (k) => clauses.filter((x) => (x.risk_level || "medium") === k).length;

  const retry = () =>
    reanalyze.mutate(id, {
      onSuccess: () => toast("Review restarted.", "success"),
      onError: (err) => toast(errorMessage(err, "Couldn't restart the review."), "error"),
    });

  const remove = () =>
    del.mutate(id, {
      onSuccess: () => {
        toast(`Deleted ${c.filename}.`, "success");
        track("contract_deleted");
        router.push("/contracts");
      },
      onError: (err) => {
        toast(errorMessage(err, "Couldn't delete the contract."), "error");
        setConfirm(false);
      },
    });

  return (
    <article>
      <Link href="/contracts" className="no-print text-sm text-muted hover:text-ink">
        Contracts
      </Link>

      <p className="hidden text-sm text-muted print:block">
        ContractIQ review, printed {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}. Flags risks to
        review; not legal advice.
      </p>
      <header className="mt-2 flex flex-col gap-6 border-b border-rule pb-8 md:flex-row md:items-end md:justify-between">
        <div className="min-w-0">
          <h1 className="break-words text-3xl sm:text-4xl">{c.filename}</h1>
          <p className="mt-2 text-sm text-muted">
            {fileKind(c)}, {fileSize(c.file_size)}, uploaded {formatDate(c.created_at)}
          </p>
          <div className="no-print mt-4 flex flex-wrap gap-2">
            {a && !notContract && (
              <button
                type="button"
                className="btn btn-primary px-3 py-1.5"
                onClick={() => {
                  track("review_printed");
                  window.print();
                }}
              >
                Save as PDF
              </button>
            )}
            {canEdit && c.status === "completed" && !notContract && (
              <button type="button" className="btn btn-quiet px-3 py-1.5" onClick={retry} disabled={reanalyze.isPending}>
                {reanalyze.isPending ? "Restarting…" : "Review again"}
              </button>
            )}
            {(canAdmin || (canEdit && c.user_id === userId)) && (
              <button type="button" className="btn btn-quiet px-3 py-1.5 text-danger" onClick={() => setConfirm(true)}>
                Delete
              </button>
            )}
          </div>
        </div>
        {a && !notContract && a.risk_score != null && <RiskMeter score={a.risk_score} level={a.risk_level} />}
      </header>

      {c.status === "processing" && <Reviewing />}
      {c.status === "failed" && <Failed onRetry={retry} busy={reanalyze.isPending} canEdit={canEdit} />}
      {c.status === "completed" && analysis.isLoading && <Loading label="Loading the review…" />}
      {c.status === "completed" && analysis.error && <ErrorNote message="Couldn't load the review." onRetry={() => analysis.refetch()} />}
      {c.status === "completed" && !analysis.isLoading && !analysis.error && !a && (
        <Failed onRetry={retry} busy={reanalyze.isPending} canEdit={canEdit} />
      )}

      {notContract && (
        <div className="mt-8 rounded-xl border border-rule bg-page p-8">
          <h2 className="text-xl">This doesn&rsquo;t look like a contract</h2>
          <p className="mt-2 max-w-[60ch] text-muted">
            {a.summary || "No agreement terms were found in this document."} Nothing was scored, and no obligations or alerts were created.
          </p>
          {canEdit && (
            <Link href="/contracts/upload" className="btn btn-primary mt-5">
              Upload a contract
            </Link>
          )}
        </div>
      )}

      {a && !notContract && (
        <div className="mt-8 grid gap-12 lg:grid-cols-[minmax(0,1fr)_18rem]">
          <div className="min-w-0">
            {(a.executive_summary || a.summary) && (
              <section aria-labelledby="summary">
                <h2 id="summary" className="text-sm font-semibold text-muted">
                  Summary
                </h2>
                <p className="mt-2 max-w-[68ch] font-serif text-xl leading-relaxed">{a.executive_summary || a.summary}</p>
              </section>
            )}

            <section aria-labelledby="clauses" className="mt-10">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <h2 id="clauses" className="text-2xl">
                  Clauses
                </h2>
                {clauses.length > 0 && (
                  <div className="no-print">
                  <Filters
                    label="Show clauses"
                    value={filter}
                    onChange={setFilter}
                    options={[
                      ["all", "All", clauses.length],
                      ["high", "High", count("high")],
                      ["medium", "Medium", count("medium")],
                      ["low", "Low", count("low")],
                    ]}
                  />
                  </div>
                )}
              </div>
              {clauses.length ? (
                <ClauseReview clauses={clauses} filter={filter} />
              ) : (
                <p className="mt-4 text-muted">No individual clauses were flagged.</p>
              )}
            </section>

            {a.recommendations?.length > 0 && (
              <section aria-labelledby="recs" className="mt-10 border-t border-rule pt-8">
                <h2 id="recs" className="text-2xl">
                  Before you sign
                </h2>
                <ol className="mt-4 list-decimal space-y-2 pl-5 marker:text-faint">
                  {a.recommendations.map((r, i) => (
                    <li key={i} className="max-w-[68ch] pl-1">
                      {r}
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </div>

          <aside className="space-y-8 lg:border-l lg:border-rule lg:pl-8">
            <div className="no-print">
              <ApprovalPanel contractId={id} contractStatus={c.status} />
            </div>
            {a.parties?.length > 0 && (
              <section aria-labelledby="parties">
                <h2 id="parties" className="text-sm font-semibold text-muted">
                  Parties
                </h2>
                <ul className="mt-2 space-y-1.5 font-serif">
                  {a.parties.map((p, i) => (
                    <li key={i}>{p}</li>
                  ))}
                </ul>
              </section>
            )}
            {a.key_dates?.length > 0 && (
              <section aria-labelledby="dates">
                <h2 id="dates" className="text-sm font-semibold text-muted">
                  Key dates
                </h2>
                <dl className="mt-2 space-y-2">
                  {a.key_dates.map((d, i) => (
                    <div key={i}>
                      <dt className="text-sm text-faint">{d.label}</dt>
                      <dd>{d.date || "Not stated"}</dd>
                    </div>
                  ))}
                </dl>
              </section>
            )}
            <section aria-labelledby="obl">
              <div className="flex items-baseline justify-between">
                <h2 id="obl" className="text-sm font-semibold text-muted">
                  Obligations
                </h2>
                <Link href="/obligations" className="text-sm text-pen hover:underline">
                  All
                </Link>
              </div>
              <div className="mt-3">
                <ContractObligations contractId={id} canEdit={canEdit} />
              </div>
            </section>
            {clauses.length > 0 && (
              <section aria-labelledby="index" className="no-print lg:sticky lg:top-24">
                <h2 id="index" className="text-sm font-semibold text-muted">
                  {clauses.length} clause{clauses.length === 1 ? "" : "s"} reviewed
                </h2>
                <div className="mt-3">
                  <RiskBar compact label="Clauses by risk" counts={{ high: count("high"), medium: count("medium"), low: count("low") }} />
                </div>
                <ol className="mt-4 space-y-1 text-sm">
                  {orderClauses(clauses).map(({ c: cl, i }) => (
                    <li key={i}>
                      <a
                        href={`#clause-${i + 1}`}
                        onClick={() => setFilter("all")}
                        className="flex items-center gap-2 rounded px-1.5 py-1 text-muted hover:bg-bg hover:text-ink"
                      >
                        <span
                          aria-hidden="true"
                          className={`h-2 w-2 shrink-0 rounded-full ${
                            { high: "bg-mark-high", medium: "bg-mark-med", low: "bg-mark-low" }[cl.risk_level] || "bg-mark-med"
                          }`}
                        />
                        <span className="truncate">{cl.clause_type || "Clause"}</span>
                        <span className="ml-auto tabular-nums text-faint">§{i + 1}</span>
                      </a>
                    </li>
                  ))}
                </ol>
              </section>
            )}
          </aside>
        </div>
      )}

      <ConfirmDelete
        open={confirm}
        onClose={() => setConfirm(false)}
        onConfirm={remove}
        busy={del.isPending}
        title="Delete this contract?"
        body={`${c.filename}, its review, obligations and alerts will be removed for good.`}
        confirmLabel="Delete contract"
      />
    </article>
  );
}