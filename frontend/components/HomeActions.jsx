"use client";

import Link from "next/link";
import { useSession } from "@/lib/session";

/** Sign-in / sign-up on the landing page, or a way back in when already signed in. */
export default function HomeActions({ compact = false }) {
  const session = useSession();

  if (session) {
    return (
      <Link href="/dashboard" className={`btn btn-primary ${compact ? "px-3 py-1.5" : "px-5 py-3"}`}>
        Open your contracts
      </Link>
    );
  }

  if (compact) {
    return (
      <nav className="flex items-center gap-1 text-sm">
        <Link href="/login" className="rounded-md px-3 py-2 text-muted hover:text-ink">
          Sign in
        </Link>
        <Link href="/register" className="btn btn-primary px-3 py-1.5">
          Create account
        </Link>
      </nav>
    );
  }

  return (
    <div className="flex flex-wrap gap-3">
      <Link href="/register" className="btn btn-primary px-5 py-3">
        Create an account
      </Link>
      <Link href="/login" className="btn btn-quiet px-5 py-3">
        Sign in
      </Link>
    </div>
  );
}