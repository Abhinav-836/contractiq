import Link from "next/link";
import Logo from "./Logo";

/** Plain reading layout for the privacy policy and terms. */
export default function LegalPage({ title, updated, children }) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-5 sm:px-6">
      <Logo />
      <article className="py-12">
        <h1 className="text-4xl">{title}</h1>
        <p className="mt-2 text-sm text-faint">Last updated {updated}</p>
        <div className="mt-8 space-y-6 leading-relaxed text-muted [&_h2]:mt-10 [&_h2]:text-xl [&_h2]:text-ink [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1.5">
          {children}
        </div>
        <p className="mt-12 flex gap-4 text-sm">
          <Link href="/" className="font-semibold text-pen underline-offset-4 hover:underline">
            Home
          </Link>
          <Link href="/privacy" className="font-semibold text-pen underline-offset-4 hover:underline">
            Privacy
          </Link>
          <Link href="/terms" className="font-semibold text-pen underline-offset-4 hover:underline">
            Terms
          </Link>
        </p>
      </article>
    </div>
  );
}
