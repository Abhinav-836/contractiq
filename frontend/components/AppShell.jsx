"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { authAPI } from "@/lib/api";
import { clearSession, saveSession, useSession } from "@/lib/session";
import { useAlertStats } from "@/lib/queries";
import { toast } from "@/lib/toast";
import Logo from "./Logo";
import { Spinner } from "./States";

const NAV = [
  { href: "/dashboard", label: "Overview" },
  { href: "/contracts", label: "Contracts" },
  { href: "/obligations", label: "Obligations" },
  { href: "/alerts", label: "Alerts", badge: "alerts" },
];

function UserMenu({ user }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
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

  const signOut = () => {
    clearSession();
    qc.clear(); // the next person in this tab must not see cached contracts
    toast("Signed out.");
    router.replace("/login");
  };

  const initials = (user?.name || user?.email || "?")
    .split(/\s+/)
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-xs font-semibold text-page"
        title={user?.name}
      >
        {initials}
      </button>
      {open && (
        <div role="menu" className="absolute right-0 top-10 z-30 w-60 rounded-lg border border-rule bg-page p-1 shadow-xl shadow-black/10">
          <div className="px-3 py-2">
            <p className="truncate font-medium">{user?.name || "Signed in"}</p>
            <p className="truncate text-sm text-muted">{user?.email}</p>
          </div>
          <div className="my-1 border-t border-rule" />
          <button type="button" role="menuitem" onClick={signOut} className="w-full rounded-md px-3 py-2 text-left text-sm hover:bg-bg">
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export default function AppShell({ children }) {
  const session = useSession();
  const router = useRouter();
  const pathname = usePathname() || "";
  const { data: alertStats } = useAlertStats(Boolean(session?.token));

  // Guard: send signed-out visitors to sign in, then back here.
  useEffect(() => {
    if (session === null) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [session, pathname, router]);

  // Tabs signed in by the old app have a token but no stored user.
  useEffect(() => {
    if (session?.token && !session.user) {
      authAPI.me().then((u) => u && saveSession(session.token, u)).catch(() => {});
    }
  }, [session]);

  if (!session) {
    return (
      <div className="flex min-h-dvh items-center justify-center text-muted" role="status">
        <Spinner className="mr-2 h-4 w-4" /> Opening ContractIQ…
      </div>
    );
  }

  const unread = alertStats?.unread || 0;

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-rule bg-page/95 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 px-4 sm:px-6">
          <div className="flex h-14 items-center">
            <Logo href="/dashboard" />
          </div>
          <nav aria-label="Main" className="order-3 -mx-4 flex w-[calc(100%+2rem)] gap-1 overflow-x-auto border-t border-rule px-3 sm:order-none sm:mx-0 sm:w-auto sm:border-0 sm:px-0">
            {NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`relative flex shrink-0 items-center gap-1.5 px-2.5 py-3 text-sm transition-colors sm:py-4 ${
                    active ? "font-semibold text-ink" : "text-muted hover:text-ink"
                  }`}
                >
                  {item.label}
                  {item.badge && unread > 0 && (
                    <span className="rounded-full bg-mark-high px-1.5 text-[11px] font-semibold leading-5 text-white" aria-label={`${unread} unread`}>
                      {unread > 99 ? "99+" : unread}
                    </span>
                  )}
                  {active && <span aria-hidden="true" className="absolute inset-x-2.5 bottom-0 h-0.5 rounded-full bg-pen" />}
                </Link>
              );
            })}
          </nav>
          <div className="ml-auto flex h-14 items-center gap-3">
            <Link href="/contracts/upload" className="btn btn-primary hidden px-3 py-1.5 sm:inline-flex">
              Upload contract
            </Link>
            <UserMenu user={session.user} />
          </div>
        </div>
      </header>
      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        {children}
      </main>
      <footer className="border-t border-rule">
        <p className="mx-auto max-w-6xl px-4 py-5 text-sm text-faint sm:px-6">
          ContractIQ flags risks to review. It isn&rsquo;t legal advice. Built by{" "}
          <a href="https://github.com/Abhinav-836" className="text-muted hover:text-ink">
            Abhinav Ashutosh
          </a>
          .
        </p>
      </footer>
    </div>
  );
}