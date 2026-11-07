"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useActiveWorkspace, useContracts, useDeleteContract } from "@/lib/queries";
import { errorMessage } from "@/lib/api";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import ContractTable from "@/components/ContractTable";
import { ConfirmDelete } from "@/components/Modal";
import { Empty, ErrorNote, Filters, Loading, PageHead } from "@/components/States";

function ContractsList() {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();
  const risk = params.get("risk") || "all";
  const [query, setQuery] = useState("");
  const [toDelete, setToDelete] = useState(null);

  const { data: contracts = [], isLoading, error, refetch } = useContracts({ limit: 100 });
  const del = useDeleteContract();
  const { canEdit, canAdmin, userId } = useActiveWorkspace();
  // Members may delete only what they uploaded; admins and owners anything.
  const canDelete = (c) => canAdmin || (canEdit && c.user_id === userId);

  const counts = useMemo(() => {
    const c = { all: contracts.length, high: 0, medium: 0, low: 0, processing: 0, failed: 0 };
    contracts.forEach((x) => {
      if (x.status === "processing" || x.status === "failed") c[x.status] += 1;
      else if (c[x.risk_level] != null) c[x.risk_level] += 1;
    });
    return c;
  }, [contracts]);

  const shown = contracts.filter((c) => {
    if (query && !c.filename?.toLowerCase().includes(query.toLowerCase())) return false;
    if (risk === "all") return true;
    if (risk === "processing" || risk === "failed") return c.status === risk;
    return c.status === "completed" && c.risk_level === risk;
  });

  const setRisk = (v) => {
    const next = new URLSearchParams(params);
    if (v === "all") next.delete("risk");
    else next.set("risk", v);
    router.replace(`${pathname}${next.size ? `?${next}` : ""}`, { scroll: false });
  };

  const options = [
    ["all", "All", counts.all],
    ["high", "High risk", counts.high],
    ["medium", "Medium", counts.medium],
    ["low", "Low", counts.low],
    ...(counts.processing ? [["processing", "Reviewing", counts.processing]] : []),
    ...(counts.failed ? [["failed", "Failed", counts.failed]] : []),
  ];

  const confirmDelete = () =>
    del.mutate(toDelete.id, {
      onSuccess: () => {
        toast(`Deleted ${toDelete.filename}.`, "success");
        track("contract_deleted");
        setToDelete(null);
      },
      onError: (err) => toast(errorMessage(err, "Couldn't delete the contract."), "error"),
    });

  return (
    <div className="space-y-8">
      <PageHead title="Contracts" sub={isLoading ? "\u00a0" : `${contracts.length} contract${contracts.length === 1 ? "" : "s"} reviewed or in review`}>
        {canEdit && (
          <Link href="/contracts/upload" className="btn btn-primary">
            Upload contract
          </Link>
        )}
      </PageHead>

      {isLoading ? (
        <Loading label="Loading contracts…" />
      ) : error ? (
        <ErrorNote message={errorMessage(error, "Couldn't load your contracts.")} onRetry={refetch} />
      ) : contracts.length === 0 ? (
        canEdit ? (
          <Empty title="No contracts yet" body="Upload a PDF, Word or text contract. Its review appears here in about a minute." action="Upload a contract" href="/contracts/upload" />
        ) : (
          <Empty title="No contracts yet" body="Nobody has uploaded a contract to this workspace yet." />
        )
      ) : (
        <>
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <Filters label="Filter by risk" value={risk} onChange={setRisk} options={options} />
            <label className="md:w-72">
              <span className="sr-only">Search by file name</span>
              <input type="search" className="field py-2" placeholder="Search by file name" value={query} onChange={(e) => setQuery(e.target.value)} />
            </label>
          </div>
          {shown.length ? (
            <ContractTable contracts={shown} onDelete={setToDelete} canDelete={canDelete} />
          ) : (
            <p className="rounded-xl border border-dashed border-rule bg-page px-6 py-10 text-center text-muted">
              No contracts match {query ? <>&ldquo;{query}&rdquo;</> : "this filter"}.
            </p>
          )}
        </>
      )}

      <ConfirmDelete
        open={Boolean(toDelete)}
        onClose={() => setToDelete(null)}
        onConfirm={confirmDelete}
        busy={del.isPending}
        title="Delete this contract?"
        body={toDelete ? `${toDelete.filename}, its review, obligations and alerts will be removed for good.` : ""}
        confirmLabel="Delete contract"
      />
    </div>
  );
}

export default function ContractsPage() {
  return (
    <Suspense fallback={<Loading />}>
      <ContractsList />
    </Suspense>
  );
}