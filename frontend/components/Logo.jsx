import Link from "next/link";

/** A page with one highlighted line — a reviewed contract. */
export function Mark({ className = "h-6 w-6" }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true" fill="none">
      <path d="M6 2.75h8.5L19 7.25V20a1.25 1.25 0 0 1-1.25 1.25H6A1.25 1.25 0 0 1 4.75 20V4A1.25 1.25 0 0 1 6 2.75Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M14.25 3v4.5H18.75" stroke="currentColor" strokeWidth="1.5" />
      <rect x="7" y="10.5" width="10" height="3" rx="1" fill="var(--hi-med)" />
      <path d="M7.75 12h8.5M7.75 16.25h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function Logo({ href = "/" }) {
  return (
    <Link href={href} className="flex items-center gap-2 text-ink">
      <Mark />
      <span className="font-serif text-lg font-semibold tracking-tight">ContractIQ</span>
    </Link>
  );
}