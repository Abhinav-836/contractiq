import Link from "next/link";
import { Mark } from "./Logo";

/*
 * Footer as the last page of a contract: link "schedules" up top, then the
 * signature block — a signed name over a rule, the signatory's role and date.
 */
const PUBLIC_LINKS = [
  ["/register", "Create an account"],
  ["/login", "Sign in"],
];
const APP_LINKS = [
  ["/dashboard", "Overview"],
  ["/contracts", "Contracts"],
  ["/obligations", "Obligations"],
  ["/alerts", "Alerts"],
];

function Signature() {
  const year = new Date().getFullYear();
  return (
    <div className="max-w-xs">
      <p className="text-xs text-faint">Built and signed by</p>
      <a href="https://github.com/Abhinav-836" className="group mt-1 block" aria-label="Abhinav Ashutosh on GitHub">
        <span aria-hidden="true" className="block font-signature text-[2.6rem] leading-none text-pen transition-transform group-hover:-rotate-1">
          Abhinav Ashutosh
        </span>
        <span className="mt-1 block border-t border-ink" />
      </a>
      <div className="mt-1.5 flex justify-between text-xs text-muted">
        <span>Abhinav Ashutosh, builder</span>
        <span className="tabular-nums">{year}</span>
      </div>
    </div>
  );
}

export default function SignatureFooter({ app = false }) {
  const links = app ? APP_LINKS : PUBLIC_LINKS;
  return (
    <footer className="no-print mt-auto border-t border-rule bg-page">
      <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        {!app && (
          <div className="grid gap-10 border-b border-rule pb-10 sm:grid-cols-[1.5fr_1fr_1fr]">
            <div>
              <p className="flex items-center gap-2 font-serif text-lg font-semibold">
                <Mark /> ContractIQ
              </p>
              <p className="mt-2 max-w-[34ch] text-muted">Every risky clause, highlighted and explained. Every obligation, tracked.</p>
            </div>
            <nav aria-label="Footer">
              <p className="text-sm font-semibold">Get started</p>
              <ul className="mt-3 space-y-2 text-sm">
                {links.map(([href, label]) => (
                  <li key={href}>
                    <Link href={href} className="text-muted hover:text-pen">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
            <div>
              <p className="text-sm font-semibold">The fine print</p>
              <ul className="mt-3 space-y-2 text-sm text-muted">
                <li>Flags risks to review. Not legal advice.</li>
                <li>Contracts are visible only to your account.</li>
                <li>PDF, Word or text, up to 20 MB.</li>
              </ul>
            </div>
          </div>
        )}

        <div className={`flex flex-col gap-8 sm:flex-row sm:items-end sm:justify-between ${app ? "" : "pt-10"}`}>
          <Signature />
          <div className="text-sm text-muted sm:text-right">
            {app ? (
              <nav aria-label="Footer" className="mb-3 flex flex-wrap gap-x-4 gap-y-1 sm:justify-end">
                {links.map(([href, label]) => (
                  <Link key={href} href={href} className="hover:text-pen">
                    {label}
                  </Link>
                ))}
              </nav>
            ) : null}
            {app && <p>ContractIQ flags risks to review. It isn&rsquo;t legal advice.</p>}
            <p className="mt-1 flex flex-wrap gap-x-4 sm:justify-end">
              <Link href="/privacy" className="hover:text-pen">
                Privacy
              </Link>
              <Link href="/terms" className="hover:text-pen">
                Terms
              </Link>
              <a href="https://github.com/Abhinav-836/contractiq" className="hover:text-pen">
                Source on GitHub
              </a>
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}