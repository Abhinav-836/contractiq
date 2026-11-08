"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { authAPI, errorMessage } from "@/lib/api";
import { saveSession } from "@/lib/session";
import { toast } from "@/lib/toast";
import AuthShell from "@/components/AuthShell";
import { Loading, Spinner } from "@/components/States";

export default function ResetPasswordPage() {
  const { token } = useParams();
  const router = useRouter();
  const qc = useQueryClient();
  const [form, setForm] = useState({ next: "", confirm: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const link = useQuery({
    queryKey: ["resetLink", token],
    queryFn: () => authAPI.checkResetLink(token),
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
  });

  const submit = async (e) => {
    e.preventDefault();
    if (form.next.length < 8) return setError("Use at least 8 characters.");
    if (form.next !== form.confirm) return setError("The two passwords don't match.");
    setBusy(true);
    setError("");
    try {
      const res = await authAPI.resetPassword(token, form.next);
      qc.clear();
      saveSession(res.access_token, res.user);
      toast("Password changed. You're signed in.", "success");
      router.replace("/dashboard");
    } catch (err) {
      setError(errorMessage(err, "Couldn't change the password."));
      setBusy(false);
    }
  };

  if (link.isLoading) {
    return (
      <AuthShell>
        <Loading label="Checking the link…" />
      </AuthShell>
    );
  }

  if (link.error) {
    return (
      <AuthShell>
        <h1 className="text-3xl">This link doesn&apos;t work</h1>
        <p className="mt-3 text-muted">
          Reset links work for 30 minutes and only once, and asking for a new one cancels the old one. Ask for a fresh link.
        </p>
        <Link href="/forgot-password" className="btn btn-primary mt-8">
          Send a new link
        </Link>
      </AuthShell>
    );
  }

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <AuthShell>
      <h1 className="text-3xl">Choose a new password</h1>
      <p className="mt-2 text-muted">
        For <span className="font-semibold text-ink">{link.data?.email}</span>
      </p>
      <form onSubmit={submit} noValidate className="mt-8 space-y-4">
        {/* Lets password managers save the new password against the right account */}
        <input type="email" autoComplete="username" value={link.data?.email || ""} readOnly hidden />
        <div>
          <label htmlFor="new" className="mb-1.5 block text-sm font-medium">
            New password
          </label>
          <input id="new" type="password" className="field" autoComplete="new-password" value={form.next} onChange={set("next")} maxLength={128} autoFocus />
          <p className="mt-1.5 text-sm text-faint">At least 8 characters. Don&apos;t reuse a password from another site.</p>
        </div>
        <div>
          <label htmlFor="confirm" className="mb-1.5 block text-sm font-medium">
            Repeat it
          </label>
          <input id="confirm" type="password" className="field" autoComplete="new-password" value={form.confirm} onChange={set("confirm")} maxLength={128} />
        </div>
        {error && (
          <p role="alert" className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary w-full py-3" disabled={busy}>
          {busy && <Spinner />} {busy ? "Saving…" : "Save and sign in"}
        </button>
      </form>
    </AuthShell>
  );
}
