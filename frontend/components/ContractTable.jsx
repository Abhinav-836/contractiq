"use client";

import Link from "next/link";
import { fileKind, fileSize, STATUS, timeAgo } from "@/lib/format";
import { RiskChip } from "./Risk";
import { Spinner } from "./States";

function Status({ c }) {
  if (c.status === "processing")
    return (
      <span className="inline-flex items-center gap-1.5 text-sm text-pen">
        <Spinner className="h-3 w-3" /> {STATUS.processing}
      </span>
    );
  if (c.status === "failed") return <span className="text-sm font-medium text-danger">{STATUS.failed}</span>;
  return c.risk_level ? <RiskChip level={c.risk_level} /> : <span className="text-sm text-muted">{STATUS[c.status] || c.status}</span>;
}

/** Contracts as a document list: name and meta left, review outcome right. */
export default function ContractTable({ contracts, onDelete, canDelete = () => true }) {
  return (
    <ul className="divide-y divide-rule overflow-hidden rounded-xl border border-rule bg-page">
      {contracts.map((c) => (
        <li key={c.id} className="group relative flex items-center gap-4 px-4 py-3.5 hover:bg-bg/60 sm:px-5">
          <span aria-hidden="true" className="hidden h-9 w-8 shrink-0 items-end justify-center rounded-sm border border-rule bg-bg pb-1 text-[9px] font-semibold text-faint sm:flex">
            {fileKind(c)}
          </span>
          <div className="min-w-0 flex-1">
            <Link href={`/contracts/${c.id}`} className="block truncate font-medium after:absolute after:inset-0 hover:text-pen">
              {c.filename}
            </Link>
            <p className="mt-0.5 text-sm text-faint">
              {fileKind(c)}, {fileSize(c.file_size)}, uploaded {timeAgo(c.created_at)}
            </p>
          </div>
          <div className="shrink-0 text-right">
            <Status c={c} />
          </div>
          {onDelete && canDelete(c) && (
            <button
              type="button"
              onClick={() => onDelete(c)}
              aria-label={`Delete ${c.filename}`}
              className="relative z-10 shrink-0 rounded-md px-2 py-1 text-sm text-faint opacity-100 hover:bg-danger/10 hover:text-danger sm:opacity-0 sm:group-hover:opacity-100 sm:focus:opacity-100"
            >
              Delete
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}