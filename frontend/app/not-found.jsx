import Link from "next/link";
import Logo from "@/components/Logo";

export const metadata = { title: "Page not found" };

export default function NotFound() {
  return (
    <div className="mx-auto flex min-h-dvh max-w-xl flex-col px-4 py-5 sm:px-6">
      <Logo />
      <div className="my-auto py-16">
        <h1 className="text-4xl">
          <span className="highlight highlight-medium">No such page</span>
        </h1>
        <p className="mt-4 text-muted">The link may be old or mistyped.</p>
        <div className="mt-8 flex flex-wrap gap-2">
          <Link href="/dashboard" className="btn btn-primary">
            Go to your contracts
          </Link>
          <Link href="/" className="btn btn-quiet">
            Home
          </Link>
        </div>
      </div>
    </div>
  );
}