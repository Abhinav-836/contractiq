"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { errorMessage, workspacesAPI } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { useActiveWorkspace, useInvites, useMembers, useWorkspaceMutation } from "@/lib/queries";
import { toast } from "@/lib/toast";
import { ROLE_HELP, ROLE_LABELS, setWorkspaceId } from "@/lib/workspace";
import { ConfirmDelete } from "@/components/Modal";
import { ErrorNote, Loading, Spinner } from "@/components/States";
import { NewWorkspaceModal } from "@/components/WorkspaceSwitcher";

const EXPIRY_OPTIONS = [
  [1, "1 day"],
  [7, "7 days"],
  [30, "30 days"],
];
const USES_OPTIONS = [
  ["", "Unlimited uses"],
  [1, "1 person"],
  [5, "5 people"],
  [25, "25 people"],
];

// Mirrors the backend rules in modules/workspaces/permissions.py
const canManage = (actor, target) => target !== "owner" && (actor === "owner" || (actor === "admin" && (target === "member" || target === "viewer")));
const grantable = (actor) => (actor === "owner" ? ["admin", "member", "viewer"] : actor === "admin" ? ["member", "viewer"] : []);

function Section({ title, sub, children, aside }) {
  return (
    <section className="rounded-xl border border-rule bg-page">
      <div className="flex flex-col gap-1 border-b border-rule px-5 py-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl">{title}</h2>
          {sub && <p className="mt-0.5 text-sm text-muted">{sub}</p>}
        </div>
        {aside}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

/* ---------------- workspace name ---------------- */
function NameEditor({ workspace, canAdmin }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(workspace.name);
  const rename = useWorkspaceMutation((n) => workspacesAPI.rename(workspace.id, n));

  useEffect(() => setName(workspace.name), [workspace.name]);

  if (!editing) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl sm:text-4xl">{workspace.name}</h1>
        {canAdmin && (
          <button type="button" className="text-sm font-semibold text-pen underline-offset-4 hover:underline" onClick={() => setEditing(true)}>
            Rename
          </button>
        )}
      </div>
    );
  }

  const save = async (e) => {
    e.preventDefault();
    if (!name.trim() || name.trim() === workspace.name) return setEditing(false);
    try {
      await rename.mutateAsync(name.trim());
      toast("Workspace renamed.", "success");
      setEditing(false);
    } catch (err) {
      toast(errorMessage(err, "Couldn't rename the workspace."), "error");
    }
  };

  return (
    <form onSubmit={save} className="flex max-w-lg flex-wrap items-center gap-2">
      <label htmlFor="ws-rename" className="sr-only">
        Workspace name
      </label>
      <input id="ws-rename" className="field min-w-0 flex-1 text-lg" value={name} maxLength={80} onChange={(e) => setName(e.target.value)} autoFocus />
      <button type="submit" className="btn btn-primary" disabled={rename.isPending}>
        {rename.isPending && <Spinner />} Save
      </button>
      <button type="button" className="btn btn-quiet" onClick={() => setEditing(false)} disabled={rename.isPending}>
        Cancel
      </button>
    </form>
  );
}

/* ---------------- members ---------------- */
function Members({ workspace, myRole }) {
  const router = useRouter();
  const { data: members = [], isLoading, error, refetch } = useMembers(workspace.id);
  const setRole = useWorkspaceMutation(({ userId, role }) => workspacesAPI.setRole(workspace.id, userId, role));
  const remove = useWorkspaceMutation((userId) => workspacesAPI.removeMember(workspace.id, userId));
  const [confirm, setConfirm] = useState(null); // member to remove (or yourself, to leave)

  const changeRole = async (m, role) => {
    try {
      await setRole.mutateAsync({ userId: m.user_id, role });
      toast(`${m.name} is now ${role === "admin" ? "an" : "a"} ${ROLE_LABELS[role].toLowerCase()}.`, "success");
    } catch (err) {
      toast(errorMessage(err, "Couldn't change the role."), "error");
    }
  };

  const doRemove = async () => {
    const m = confirm;
    try {
      await remove.mutateAsync(m.user_id);
      setConfirm(null);
      if (m.is_you) {
        setWorkspaceId(null);
        toast(`You left ${workspace.name}.`);
        router.push("/dashboard");
      } else {
        toast(`${m.name} was removed.`);
      }
    } catch (err) {
      toast(errorMessage(err, "Couldn't remove them."), "error");
    }
  };

  const options = grantable(myRole);

  return (
    <Section title="People" sub={`${members.length || workspace.member_count} with access`}>
      {isLoading ? (
        <Loading label="Loading people…" />
      ) : error ? (
        <ErrorNote message={errorMessage(error, "Couldn't load the people in this workspace.")} onRetry={refetch} />
      ) : (
        <ul className="divide-y divide-rule">
          {members.map((m) => {
            const manageable = !m.is_you && canManage(myRole, m.role);
            return (
              <li key={m.user_id} className="flex flex-wrap items-center gap-x-4 gap-y-2 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">
                    {m.name} {m.is_you && <span className="text-sm font-normal text-muted">(you)</span>}
                  </p>
                  <p className="truncate text-sm text-muted">{m.email}</p>
                </div>
                {manageable ? (
                  <>
                    <label htmlFor={`role-${m.user_id}`} className="sr-only">
                      Role for {m.name}
                    </label>
                    <select
                      id={`role-${m.user_id}`}
                      className="field w-auto py-1.5 text-sm"
                      value={m.role}
                      disabled={setRole.isPending}
                      onChange={(e) => changeRole(m, e.target.value)}
                    >
                      {[...new Set([m.role, ...options])].map((r) => (
                        <option key={r} value={r}>
                          {ROLE_LABELS[r]}
                        </option>
                      ))}
                    </select>
                    <button type="button" className="text-sm font-semibold text-danger underline-offset-4 hover:underline" onClick={() => setConfirm(m)}>
                      Remove
                    </button>
                  </>
                ) : (
                  <span className="rounded-full bg-bg px-2.5 py-0.5 text-sm text-muted">{ROLE_LABELS[m.role] || m.role}</span>
                )}
                {m.is_you && m.role !== "owner" && (
                  <button type="button" className="text-sm font-semibold text-danger underline-offset-4 hover:underline" onClick={() => setConfirm(m)}>
                    Leave
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmDelete
        open={Boolean(confirm)}
        onClose={() => setConfirm(null)}
        onConfirm={doRemove}
        busy={remove.isPending}
        title={confirm?.is_you ? `Leave ${workspace.name}?` : `Remove ${confirm?.name}?`}
        body={
          confirm?.is_you
            ? "You'll lose access to its contracts. Someone will need to invite you again to come back."
            : `They'll lose access to ${workspace.name} straight away. Contracts they uploaded stay in the workspace.`
        }
        confirmLabel={confirm?.is_you ? "Leave" : "Remove"}
      />
    </Section>
  );
}

/* ---------------- invite links ---------------- */
function Invites({ workspace, myRole }) {
  const { data: invites = [], isLoading } = useInvites(workspace.id, true);
  const create = useWorkspaceMutation((body) => workspacesAPI.createInvite(workspace.id, body));
  const revoke = useWorkspaceMutation((id) => workspacesAPI.revokeInvite(workspace.id, id));
  const roles = grantable(myRole);
  const [form, setForm] = useState({ role: "member", expires_in_days: 7, max_uses: "" });
  const [link, setLink] = useState(null); // { url, role } — the token is shown only once
  const [copied, setCopied] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    try {
      const inv = await create.mutateAsync({
        role: form.role,
        expires_in_days: Number(form.expires_in_days),
        max_uses: form.max_uses === "" ? null : Number(form.max_uses),
      });
      setLink({ url: `${window.location.origin}/invite/${inv.token}`, role: inv.role });
      setCopied(false);
    } catch (err) {
      toast(errorMessage(err, "Couldn't create the invite link."), "error");
    }
  };

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(link.url);
      setCopied(true);
      toast("Invite link copied.", "success");
    } catch {
      toast("Couldn't copy. Select the link and copy it manually.", "error");
    }
  };

  const doRevoke = async (id) => {
    try {
      await revoke.mutateAsync(id);
      toast("Invite link revoked. It no longer works.");
    } catch (err) {
      toast(errorMessage(err, "Couldn't revoke the link."), "error");
    }
  };

  return (
    <Section title="Invite links" sub="Anyone with a link can join with the role you pick, until it expires or runs out.">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[1fr_1fr_1fr_auto] sm:items-end">
        <div>
          <label htmlFor="inv-role" className="mb-1.5 block text-sm font-medium">
            Joins as
          </label>
          <select id="inv-role" className="field" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
            {roles.map((r) => (
              <option key={r} value={r}>
                {ROLE_LABELS[r]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="inv-exp" className="mb-1.5 block text-sm font-medium">
            Expires after
          </label>
          <select id="inv-exp" className="field" value={form.expires_in_days} onChange={(e) => setForm({ ...form, expires_in_days: e.target.value })}>
            {EXPIRY_OPTIONS.map(([v, l]) => (
              <option key={v} value={v}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="inv-uses" className="mb-1.5 block text-sm font-medium">
            Can be used by
          </label>
          <select id="inv-uses" className="field" value={form.max_uses} onChange={(e) => setForm({ ...form, max_uses: e.target.value })}>
            {USES_OPTIONS.map(([v, l]) => (
              <option key={l} value={v}>
                {l}
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className="btn btn-primary" disabled={create.isPending}>
          {create.isPending && <Spinner />} Create link
        </button>
      </form>
      <p className="mt-2 text-sm text-faint">{ROLE_HELP[form.role]}</p>

      {link && (
        <div className="mt-4 rounded-lg border border-pen/40 bg-bg p-3">
          <p className="text-sm font-medium">
            New {ROLE_LABELS[link.role].toLowerCase()} link. Copy it now: it won&apos;t be shown again.
          </p>
          <div className="mt-2 flex flex-col gap-2 sm:flex-row">
            <label htmlFor="inv-link" className="sr-only">
              Invite link
            </label>
            <input id="inv-link" readOnly className="field min-w-0 flex-1 font-mono text-sm" value={link.url} onFocus={(e) => e.target.select()} />
            <button type="button" className="btn btn-quiet" onClick={copy}>
              {copied ? "Copied" : "Copy link"}
            </button>
          </div>
        </div>
      )}

      <h3 className="mt-6 text-sm font-semibold">Active links</h3>
      {isLoading ? (
        <Loading label="Loading links…" />
      ) : invites.length === 0 ? (
        <p className="mt-1 text-sm text-muted">No active invite links.</p>
      ) : (
        <ul className="mt-2 divide-y divide-rule">
          {invites.map((inv) => (
            <li key={inv.id} className="flex flex-wrap items-center gap-x-4 gap-y-1 py-2.5 text-sm">
              <span className="font-medium">{ROLE_LABELS[inv.role]}</span>
              <span className="text-muted">
                {inv.max_uses ? `${inv.use_count} of ${inv.max_uses} used` : `${inv.use_count} joined`} · expires {formatDate(inv.expires_at)}
                {inv.created_by_name ? ` · by ${inv.created_by_name}` : ""}
              </span>
              <button
                type="button"
                className="ml-auto font-semibold text-danger underline-offset-4 hover:underline"
                onClick={() => doRevoke(inv.id)}
                disabled={revoke.isPending}
              >
                Revoke
              </button>
            </li>
          ))}
        </ul>
      )}
    </Section>
  );
}

/* ---------------- danger zone ---------------- */
function DeleteWorkspace({ workspace }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const del = useWorkspaceMutation(() => workspacesAPI.remove(workspace.id));
  const hasContracts = workspace.contract_count > 0;

  const doDelete = async () => {
    try {
      await del.mutateAsync();
      setOpen(false);
      setWorkspaceId(null);
      toast(`${workspace.name} was deleted.`);
      router.push("/dashboard");
    } catch (err) {
      toast(errorMessage(err, "Couldn't delete the workspace."), "error");
    }
  };

  return (
    <Section title="Delete workspace">
      <p className="text-muted">
        {hasContracts
          ? `Delete its ${workspace.contract_count} contract${workspace.contract_count === 1 ? "" : "s"} first. A workspace can only be deleted when it's empty.`
          : "Everyone loses access and its invite links stop working. This can't be undone."}
      </p>
      <button type="button" className="btn btn-danger mt-4" disabled={hasContracts} onClick={() => setOpen(true)}>
        Delete workspace
      </button>
      <ConfirmDelete
        open={open}
        onClose={() => setOpen(false)}
        onConfirm={doDelete}
        busy={del.isPending}
        title={`Delete ${workspace.name}?`}
        body={`All ${workspace.member_count} ${workspace.member_count === 1 ? "person" : "people"} lose access. This can't be undone.`}
        confirmLabel="Delete workspace"
      />
    </Section>
  );
}

/* ---------------- page ---------------- */
export default function TeamPage() {
  const { active, role, canAdmin, isOwner, isLoading } = useActiveWorkspace();
  const [creating, setCreating] = useState(false);

  if (isLoading || !active) return <Loading label="Loading your workspace…" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <NameEditor workspace={active} canAdmin={canAdmin} />
          <p className="mt-2 text-muted">
            You&apos;re {role === "owner" ? "the owner" : `${role === "admin" ? "an" : "a"} ${ROLE_LABELS[role]?.toLowerCase()}`}
            {active.is_personal ? " · your personal workspace" : ""} · {active.contract_count} contract{active.contract_count === 1 ? "" : "s"}
          </p>
        </div>
        <button type="button" className="btn btn-quiet self-start sm:self-auto" onClick={() => setCreating(true)}>
          New workspace
        </button>
      </div>

      {active.is_personal && active.member_count === 1 && (
        <p className="rounded-lg border border-rule bg-bg px-4 py-3 text-sm text-muted">
          This is your personal workspace. To review contracts with others, invite them here, or create a separate workspace for the team.
        </p>
      )}

      <Members workspace={active} myRole={role} />
      {canAdmin && <Invites workspace={active} myRole={role} />}
      {isOwner && !active.is_personal && <DeleteWorkspace workspace={active} />}

      <NewWorkspaceModal open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
