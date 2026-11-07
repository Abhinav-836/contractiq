"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useQueryClient } from "@tanstack/react-query";
import { usePathname, useRouter } from "next/navigation";
import { workspacesAPI, errorMessage } from "@/lib/api";
import { useActiveWorkspace, useWorkspaceMutation } from "@/lib/queries";
import { toast } from "@/lib/toast";
import { ROLE_LABELS, setWorkspaceId } from "@/lib/workspace";
import Modal from "./Modal";
import { Spinner } from "./States";

/** Switch to a workspace; leave pages that belong to the old one. */
export function useSwitchTo() {
  const router = useRouter();
  const pathname = usePathname() || "";
  return (id) => {
    setWorkspaceId(id);
    // A contract page belongs to the workspace it was opened in.
    if (/^\/contracts\/(?!upload)[^/]+/.test(pathname)) router.push("/contracts");
  };
}

export function NewWorkspaceModal({ open, onClose }) {
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const switchTo = useSwitchTo();
  const router = useRouter();
  const qc = useQueryClient();
  const create = useWorkspaceMutation((n) => workspacesAPI.create(n));

  useEffect(() => {
    if (open) {
      setName("");
      setError("");
    }
  }, [open]);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return setError("Give the workspace a name.");
    try {
      const ws = await create.mutateAsync(name.trim());
      // Put it in the list before switching, so the app never sees an
      // unknown workspace id and falls back to the personal one.
      qc.setQueryData(["workspaces"], (list) => (list?.some((w) => w.id === ws.id) ? list : [...(list || []), ws]));
      onClose();
      switchTo(ws.id);
      toast(`Created ${ws.name}. Invite your team from here.`, "success");
      router.push("/team");
    } catch (err) {
      setError(errorMessage(err, "Couldn't create the workspace."));
    }
  };

  return (
    <Modal open={open} onClose={() => !create.isPending && onClose()} title="New workspace">
      <form onSubmit={submit} noValidate>
        <p className="text-muted">A shared space for a team&apos;s contracts. You&apos;ll be its owner.</p>
        <label htmlFor="ws-name" className="mb-1.5 mt-4 block text-sm font-medium">
          Name
        </label>
        <input
          id="ws-name"
          className="field"
          value={name}
          maxLength={80}
          placeholder="e.g. Legal team"
          onChange={(e) => setName(e.target.value)}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? "ws-name-err" : undefined}
          autoFocus
        />
        {error && (
          <p id="ws-name-err" className="mt-1.5 text-sm text-danger">
            {error}
          </p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <button type="button" className="btn btn-quiet" onClick={onClose} disabled={create.isPending}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={create.isPending}>
            {create.isPending && <Spinner />} Create workspace
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function WorkspaceSwitcher() {
  const { workspaces, active } = useActiveWorkspace();
  const switchTo = useSwitchTo();
  const [open, setOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false);
    const esc = (e) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", close);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", close);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);

  if (!active) return null;

  return (
    <div ref={ref} className="relative min-w-0">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex max-w-[11rem] items-center gap-1.5 rounded-md border border-rule px-2.5 py-1.5 text-sm hover:border-faint sm:max-w-[15rem]"
        title={`Workspace: ${active.name}`}
      >
        <span className="truncate font-medium">{active.name}</span>
        <svg aria-hidden="true" viewBox="0 0 16 16" className="h-3.5 w-3.5 shrink-0 text-muted">
          <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <div role="menu" className="absolute right-0 top-10 z-30 w-72 rounded-lg border border-rule bg-page p-1 shadow-xl shadow-black/10 sm:left-0 sm:right-auto">
          <p className="px-3 pb-1 pt-2 text-xs font-semibold uppercase tracking-wide text-faint">Workspaces</p>
          <ul>
            {workspaces.map((w) => {
              const current = w.id === active.id;
              return (
                <li key={w.id}>
                  <button
                    type="button"
                    role="menuitemradio"
                    aria-checked={current}
                    onClick={() => {
                      setOpen(false);
                      if (!current) switchTo(w.id);
                    }}
                    className={`flex w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm hover:bg-bg ${current ? "font-semibold" : ""}`}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate">{w.name}</span>
                      <span className="block text-xs font-normal text-muted">
                        {ROLE_LABELS[w.role] || w.role} · {w.member_count} {w.member_count === 1 ? "person" : "people"}
                      </span>
                    </span>
                    {current && (
                      <svg aria-hidden="true" viewBox="0 0 16 16" className="h-4 w-4 shrink-0 text-pen">
                        <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
          <div className="my-1 border-t border-rule" />
          <Link href="/team" role="menuitem" onClick={() => setOpen(false)} className="block rounded-md px-3 py-2 text-sm hover:bg-bg">
            Team &amp; invites
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              setOpen(false);
              setCreating(true);
            }}
            className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-bg"
          >
            New workspace…
          </button>
        </div>
      )}

      <NewWorkspaceModal open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
