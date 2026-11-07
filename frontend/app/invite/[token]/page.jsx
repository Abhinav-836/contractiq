"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { errorMessage, invitesAPI } from "@/lib/api";
import { useSession } from "@/lib/session";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import { ROLE_HELP, ROLE_LABELS, setWorkspaceId } from "@/lib/workspace";
import Logo from "@/components/Logo";
import { Loading, Spinner } from "@/components/States";

export default function InvitePage() {
  const { token } = useParams();
  const router = useRouter();
  const qc = useQueryClient();
  const session = useSession();
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState("");

  const preview = useQuery({
    queryKey: ["invitePreview", token],
    queryFn: () => invitesAPI.preview(token),
    enabled: Boolean(token),
    retry: false,
  });
  const invite = preview.data;
  const next = encodeURIComponent(`/invite/${token}`);

  const join = async () => {
    setJoining(true);
    setJoinError("");
    try {
      const res = await invitesAPI.accept(token);
      track("invite_accepted", { role: res.role });
      // Refresh the list first so the new workspace is known before it's selected.
      await qc.refetchQueries({ queryKey: ["workspaces"] });
      setWorkspaceId(res.workspace_id);
      toast(
        res.already_member ? `You're already in ${invite.workspace_name}. Switched to it.` : `You joined ${invite.workspace_name}.`,
        "success",
      );
      router.replace("/dashboard");
    } catch (err) {
      setJoinError(errorMessage(err, "Couldn't join the workspace."));
      setJoining(false);
    }
  };

  let body;
  if (preview.isLoading || session === undefined) {
    body = <Loading label="Checking the invite…" />;
  } else if (preview.error) {
    body = (
      <>
        <h1 className="text-3xl">This invite doesn&apos;t work</h1>
        <p className="mt-3 text-muted">
          {preview.error?.response?.status === 404
            ? "It may have expired, been revoked, or already been used by as many people as allowed. Ask whoever sent it for a new link."
            : errorMessage(preview.error)}
        </p>
        <Link href={session ? "/dashboard" : "/login"} className="btn btn-quiet mt-6">
          {session ? "Go to your dashboard" : "Sign in"}
        </Link>
      </>
    );
  } else {
    const role = ROLE_LABELS[invite.role] || invite.role;
    body = (
      <>
        <p className="text-sm font-semibold uppercase tracking-wide text-faint">Invitation</p>
        <h1 className="mt-2 text-3xl">Join {invite.workspace_name}</h1>
        <p className="mt-3 text-muted">
          {invite.invited_by ? `${invite.invited_by} invited you` : "You've been invited"} as {role === "Admin" ? "an" : "a"}{" "}
          <span className="font-semibold text-ink">{role.toLowerCase()}</span>. {ROLE_HELP[invite.role]}
        </p>

        {joinError && (
          <p role="alert" className="mt-5 rounded-lg border border-danger/30 bg-danger/5 px-3 py-2.5 text-sm text-danger">
            {joinError}
          </p>
        )}

        {session ? (
          <>
            <button type="button" className="btn btn-primary mt-6 w-full py-3" onClick={join} disabled={joining}>
              {joining && <Spinner />} {joining ? "Joining…" : `Join ${invite.workspace_name}`}
            </button>
            <p className="mt-3 text-sm text-muted">
              Signed in as {session.user?.email || "you"}. Your own contracts stay in your personal workspace.
            </p>
          </>
        ) : (
          <div className="mt-6 flex flex-col gap-2">
            <Link href={`/register?next=${next}`} className="btn btn-primary py-3">
              Create an account to join
            </Link>
            <Link href={`/login?next=${next}`} className="btn btn-quiet py-3">
              I already have an account
            </Link>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6">
        <Logo href={session ? "/dashboard" : "/"} />
      </header>
      <main className="flex flex-1 items-start justify-center px-4 pb-16 pt-6 sm:items-center sm:pt-0">
        <div className="w-full max-w-md">{body}</div>
      </main>
    </div>
  );
}
