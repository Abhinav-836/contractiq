"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { authAPI, errorMessage } from "@/lib/api";
import { saveSession, useSession } from "@/lib/session";
import AuthShell from "@/components/AuthShell";
import { Loading } from "@/components/States";

export default function VerifyEmailPage() {
  const { token } = useParams();
  const session = useSession();
  const [state, setState] = useState({ status: "working" });
  const started = useRef(false);

  useEffect(() => {
    // Run once, after the session has loaded (so a signed-in tab can be updated too).
    if (!token || session === undefined || started.current) return;
    started.current = true;
    authAPI
      .verifyEmail(token)
      .then((user) => {
        if (session?.token && session.user?.id === user.id) saveSession(session.token, user);
        setState({ status: "done", user });
      })
      .catch((err) => setState({ status: "failed", message: errorMessage(err, "This link doesn't work.") }));
  }, [token, session]);

  let body;
  if (state.status === "working") {
    body = <Loading label="Confirming your email…" />;
  } else if (state.status === "done") {
    body = (
      <>
        <h1 className="text-3xl">Email confirmed</h1>
        <p className="mt-3 text-muted">
          <span className="font-semibold text-ink">{state.user.email}</span> is confirmed. You can now email signing requests,
          reminders and team invites.
        </p>
        <Link href={session ? "/dashboard" : "/login"} className="btn btn-primary mt-8">
          {session ? "Go to your dashboard" : "Sign in"}
        </Link>
      </>
    );
  } else {
    body = (
      <>
        <h1 className="text-3xl">This link doesn&apos;t work</h1>
        <p className="mt-3 text-muted">{state.message}</p>
        <p className="mt-3 text-sm text-faint">Sign in and use “Resend email” in the banner at the top to get a new link.</p>
        <Link href={session ? "/dashboard" : "/login"} className="btn btn-primary mt-8">
          {session ? "Go to your dashboard" : "Sign in"}
        </Link>
      </>
    );
  }
  return <AuthShell>{body}</AuthShell>;
}
