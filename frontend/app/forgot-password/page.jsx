"use client";

import { useState } from "react";
import Link from "next/link";
import { authAPI, errorMessage } from "@/lib/api";
import AuthShell from "@/components/AuthShell";
import { Spinner } from "@/components/States";

const EMAIL_RE = /^\S+@\S+\.\S+$/;

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sentTo, setSentTo] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    const value = email.trim();
    if (!EMAIL_RE.test(value)) {
      setError("Enter the email address you sign in with.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await authAPI.forgotPassword(value);
      setSentTo(value);
    } catch (err) {
      setError(errorMessage(err, "Couldn't send the reset email. Try again in a minute."));
    } finally {
      setBusy(false);
    }
  };

  if (sentTo) {
    return (
      <AuthShell>
        <h1 className="text-3xl">Check your email</h1>
        <p className="mt-3 text-muted">
          If <span className="font-semibold text-ink">{sentTo}</span> has a ContractIQ account, a link to choose a new password is
          on its way. It works for 30 minutes.
        </p>
        <p className="mt-3 text-sm text-faint">Nothing after a few minutes? Check your spam folder, or make sure you typed the address you signed up with.</p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/login" className="btn btn-primary">
            Back to sign in
          </Link>
          <button type="button" className="btn btn-quiet" onClick={() => setSentTo("")}>
            Use another email
          </button>
        </div>
      </AuthShell>
    );
  }

  return (
    <AuthShell>
      <h1 className="text-3xl">Forgot your password?</h1>
      <p className="mt-2 text-muted">Enter your email and we&apos;ll send you a link to choose a new one.</p>
      <form onSubmit={submit} noValidate className="mt-8 space-y-4">
        <div>
          <label htmlFor="email" className="mb-1.5 block text-sm font-medium">
            Email
          </label>
          <input
            id="email"
            type="email"
            className="field"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            aria-invalid={Boolean(error)}
            autoFocus
          />
        </div>
        {error && (
          <p role="alert" className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}
        <button type="submit" className="btn btn-primary w-full py-3" disabled={busy}>
          {busy && <Spinner />} {busy ? "Sending…" : "Send reset link"}
        </button>
      </form>
      <p className="mt-6 text-sm text-muted">
        Remembered it?{" "}
        <Link href="/login" className="font-semibold text-pen underline-offset-4 hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
