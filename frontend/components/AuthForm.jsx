"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { authAPI, errorMessage } from "@/lib/api";
import { useFeatures } from "@/lib/queries";
import { saveSession, useSession } from "@/lib/session";
import { toast } from "@/lib/toast";
import { track } from "@/lib/track";
import GoogleButton from "./GoogleButton";
import Logo from "./Logo";
import { Spinner } from "./States";

const EMAIL_RE = /^\S+@\S+\.\S+$/;

// Only allow in-app paths as the post-login destination.
const safeNext = (n) => (n && n.startsWith("/") && !n.startsWith("//") ? n : "/dashboard");

function Field({ id, label, error, hint, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <input id={id} className="field" aria-invalid={Boolean(error)} aria-describedby={error ? `${id}-err` : hint ? `${id}-hint` : undefined} {...props} />
      {error ? (
        <p id={`${id}-err`} className="mt-1.5 text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={`${id}-hint`} className="mt-1.5 text-sm text-faint">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export default function AuthForm({ mode }) {
  const isRegister = mode === "register";
  const router = useRouter();
  const params = useSearchParams();
  const session = useSession();
  const qc = useQueryClient();
  const next = safeNext(params.get("next"));
  const { data: features } = useFeatures();

  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState(params.get("expired") ? "Your session ended. Sign in again to continue." : "");
  const [busy, setBusy] = useState(false);
  const submitted = useRef(false);

  // Already signed in when the page opened → skip the form. (After a fresh
  // sign-in, submit() decides where to go instead.)
  useEffect(() => {
    if (session && !submitted.current) router.replace(next);
  }, [session, next, router]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const validate = () => {
    const e = {};
    if (isRegister && !form.name.trim()) e.name = "Enter your name.";
    if (!form.email.trim()) e.email = "Enter your email address.";
    else if (!EMAIL_RE.test(form.email.trim())) e.email = "That email address doesn't look right.";
    if (!form.password) e.password = "Enter your password.";
    else if (isRegister && form.password.length < 8) e.password = "Use at least 8 characters.";
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  /** Signed in (by password or Google): keep the session and move on. */
  const finish = (res, created, via) => {
    submitted.current = true;
    qc.clear(); // drop anything cached from a previous account in this tab
    saveSession(res.access_token, res.user);
    track(created ? "signed_up" : "signed_in", { via });
    const first = res.user?.name?.split(" ")[0] || "there";
    toast(
      created
        ? res.user?.email_verified === false
          ? `Account created, ${first}. We emailed ${res.user.email} a link to confirm it.`
          : `Account created. Welcome, ${first}.`
        : `Welcome back, ${first}.`,
      "success",
    );
    // A new account goes straight to its first upload — unless it came from
    // a link (e.g. an invite) that asked to come back.
    router.replace(created && !params.get("next") ? "/contracts/upload" : next);
  };

  const withGoogle = async (credential) => {
    if (busy) return;
    setFormError("");
    setBusy(true);
    try {
      const res = await authAPI.google(credential);
      finish(res, Boolean(res.created), "google");
    } catch (err) {
      setFormError(errorMessage(err, "Couldn't sign you in with Google."));
      setBusy(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setFormError("");
    if (!validate() || busy) return;
    setBusy(true);
    try {
      const res = isRegister
        ? await authAPI.register({ name: form.name.trim(), email: form.email.trim(), password: form.password })
        : await authAPI.login(form.email.trim(), form.password);
      finish(res, isRegister, "password");
    } catch (err) {
      const status = err?.response?.status;
      const detail = err?.response?.data?.detail;
      setFormError(
        !isRegister && status === 401
          ? typeof detail === "string" && detail.includes("Google")
            ? detail
            : "That email and password don't match an account."
          : errorMessage(err, isRegister ? "Couldn't create the account." : "Couldn't sign you in."),
      );
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto w-full max-w-6xl px-4 py-5 sm:px-6">
        <Logo />
      </header>
      <main className="flex flex-1 items-start justify-center px-4 pb-16 pt-6 sm:items-center sm:pt-0">
        <div className="w-full max-w-sm">
          <h1 className="text-3xl">{isRegister ? "Create your account" : "Sign in"}</h1>
          <p className="mt-2 text-muted">
            {isRegister ? "Then upload a contract to see its first review." : "Pick up where you left off with your contracts."}
          </p>

          {features?.google_client_id && (
            <div className="mt-8">
              <GoogleButton
                clientId={features.google_client_id}
                text={isRegister ? "signup_with" : "continue_with"}
                onCredential={withGoogle}
                disabled={busy}
              />
              <div className="mt-6 flex items-center gap-3 text-xs uppercase tracking-wide text-faint" aria-hidden="true">
                <span className="h-px flex-1 bg-rule" />
                or with email
                <span className="h-px flex-1 bg-rule" />
              </div>
            </div>
          )}

          <form onSubmit={submit} noValidate className={`${features?.google_client_id ? "mt-6" : "mt-8"} space-y-4`}>
            {isRegister && <Field id="name" label="Your name" autoComplete="name" value={form.name} onChange={set("name")} error={errors.name} maxLength={100} />}
            <Field id="email" label="Work email" type="email" autoComplete="email" inputMode="email" value={form.email} onChange={set("email")} error={errors.email} />
            <Field
              id="password"
              label="Password"
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
              value={form.password}
              onChange={set("password")}
              error={errors.password}
              hint={isRegister ? "At least 8 characters." : undefined}
              maxLength={128}
            />

            {!isRegister && features?.email && (
              <p className="-mt-2 text-right text-sm">
                <Link href="/forgot-password" className="font-semibold text-pen underline-offset-4 hover:underline">
                  Forgot password?
                </Link>
              </p>
            )}

            {formError && (
              <p role="alert" className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2.5 text-sm text-danger">
                {formError}
              </p>
            )}

            <button type="submit" className="btn btn-primary w-full py-3" disabled={busy}>
              {busy && <Spinner />}
              {isRegister ? (busy ? "Creating account…" : "Create account") : busy ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-sm text-muted">
            {isRegister ? "Already have an account? " : "New to ContractIQ? "}
            <Link
              href={`${isRegister ? "/login" : "/register"}${params.get("next") ? `?next=${encodeURIComponent(next)}` : ""}`}
              className="font-semibold text-pen underline-offset-4 hover:underline"
            >
              {isRegister ? "Sign in" : "Create an account"}
            </Link>
          </p>
        </div>
      </main>
    </div>
  );
}