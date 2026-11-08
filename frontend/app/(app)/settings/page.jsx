"use client";

import { useEffect, useState } from "react";
import { authAPI, errorMessage } from "@/lib/api";
import { saveSession, useSession } from "@/lib/session";
import { toast } from "@/lib/toast";
import { Spinner } from "@/components/States";

function Section({ title, sub, children }) {
  return (
    <section className="rounded-xl border border-rule bg-page">
      <div className="border-b border-rule px-5 py-4">
        <h2 className="text-xl">{title}</h2>
        {sub && <p className="mt-0.5 text-sm text-muted">{sub}</p>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </section>
  );
}

function Field({ id, label, hint, ...props }) {
  return (
    <div>
      <label htmlFor={id} className="mb-1.5 block text-sm font-medium">
        {label}
      </label>
      <input id={id} className="field w-full" {...props} />
      {hint && <p className="mt-1 text-xs text-faint">{hint}</p>}
    </div>
  );
}

/** Save the change, then keep this tab signed in with the fresh token. */
async function update(body) {
  const out = await authAPI.updateMe(body);
  saveSession(out.access_token, out.user);
  return out.user;
}

function ProfileForm({ user }) {
  const [name, setName] = useState(user?.name || "");
  const [busy, setBusy] = useState(false);
  useEffect(() => setName(user?.name || ""), [user?.name]);
  const unchanged = name.trim().replace(/\s+/g, " ") === (user?.name || "");

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await update({ name: name.trim() });
      toast("Name updated.", "success");
    } catch (err) {
      toast(errorMessage(err, "Couldn't update your name."), "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section title="Your name" sub="Shown to your team, on approval requests and on signing emails you send.">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-end">
        <Field id="acc-name" label="Name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={120} autoComplete="name" />
        <button type="submit" className="btn btn-primary" disabled={busy || unchanged || !name.trim()}>
          {busy && <Spinner />} Save name
        </button>
      </form>
    </Section>
  );
}

function EmailForm({ user }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const u = await update({ email: email.trim(), current_password: password });
      toast(
        u.email_verified === false
          ? `Email changed to ${u.email}. Use it to sign in — and click the link we sent there to confirm it.`
          : `Email changed to ${u.email}. Use it next time you sign in.`,
        "success",
      );
      setEmail("");
      setPassword("");
    } catch (err) {
      toast(errorMessage(err, "Couldn't change your email."), "error");
    } finally {
      setBusy(false);
    }
  };

  return (
    <Section
      title="Email address"
      sub="You sign in with this, and signing and approval emails about your requests are sent here."
    >
      <p className="mb-4 text-sm">
        Current: <span className="font-medium">{user?.email}</span>
      </p>
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-2">
        <Field id="acc-email" label="New email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        <Field
          id="acc-email-pw"
          label="Current password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          autoComplete="current-password"
        />
        <div className="sm:col-span-2">
          <button type="submit" className="btn btn-primary" disabled={busy || !email.trim() || !password}>
            {busy && <Spinner />} Change email
          </button>
        </div>
      </form>
    </Section>
  );
}

function PasswordForm() {
  const [form, setForm] = useState({ current: "", next: "", confirm: "" });
  const [busy, setBusy] = useState(false);
  const mismatch = form.confirm && form.next !== form.confirm;

  const submit = async (e) => {
    e.preventDefault();
    if (form.next !== form.confirm) return;
    setBusy(true);
    try {
      await update({ new_password: form.next, current_password: form.current });
      toast("Password changed.", "success");
      setForm({ current: "", next: "", confirm: "" });
    } catch (err) {
      toast(errorMessage(err, "Couldn't change your password."), "error");
    } finally {
      setBusy(false);
    }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  return (
    <Section title="Password">
      <form onSubmit={submit} className="grid gap-3 sm:grid-cols-3">
        <Field id="pw-current" label="Current password" type="password" value={form.current} onChange={set("current")} required autoComplete="current-password" />
        <Field
          id="pw-new"
          label="New password"
          type="password"
          value={form.next}
          onChange={set("next")}
          required
          minLength={8}
          maxLength={128}
          autoComplete="new-password"
          hint="At least 8 characters."
        />
        <Field
          id="pw-confirm"
          label="Repeat new password"
          type="password"
          value={form.confirm}
          onChange={set("confirm")}
          required
          autoComplete="new-password"
          hint={mismatch ? "The passwords don't match." : undefined}
        />
        <div className="sm:col-span-3">
          <button type="submit" className="btn btn-primary" disabled={busy || !form.current || form.next.length < 8 || form.next !== form.confirm}>
            {busy && <Spinner />} Change password
          </button>
        </div>
      </form>
    </Section>
  );
}

export default function SettingsPage() {
  const session = useSession();
  const user = session?.user;
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl">Account settings</h1>
        <p className="mt-2 text-muted">Your name, sign-in email and password.</p>
      </div>
      <ProfileForm user={user} />
      <EmailForm user={user} />
      <PasswordForm />
    </div>
  );
}
