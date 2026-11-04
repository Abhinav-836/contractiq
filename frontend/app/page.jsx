import Link from "next/link";
import Logo from "@/components/Logo";
import MarkedPage from "@/components/MarkedPage";
import HomeActions from "@/components/HomeActions";
import ReviewPreview from "@/components/ReviewPreview";
import SignatureFooter from "@/components/SignatureFooter";

const CATCHES = [
  ["high", "One-sided liability caps", "Their exposure is capped, yours isn't."],
  ["high", "Indemnities for their mistakes", "You cover claims the other side caused."],
  ["high", "Termination you can't use", "They can leave in weeks; you can't."],
  ["medium", "Silent auto-renewals", "Miss a notice date and you're in for another year."],
  ["medium", "Steep late-payment interest", "Rates far above normal commercial terms."],
  ["medium", "Broad IP assignment", "Work you'd reuse ends up belonging to them."],
  ["low", "Governing law and courts", "Where a dispute would be heard."],
  ["low", "Confidentiality periods", "How long each side has to keep quiet."],
];

const FOR = [
  ["Founders", "Signing vendor, SaaS and service agreements without a lawyer on every deal."],
  ["Freelancers and agencies", "Checking a client's MSA or SOW for payment terms and IP grabs before saying yes."],
  ["Ops and procurement", "Keeping renewals, notice dates and obligations from slipping across many contracts."],
];

const STEPS = [
  ["Upload the contract", "A text PDF, Word (.docx) or plain-text file, up to 20 MB."],
  ["Read the mark-up", "Each clause is scored low, medium or high risk, with what to ask for instead."],
  ["Keep track", "Obligations and alerts stay with the contract after you sign."],
];

const FAQ = [
  [
    "Is this legal advice?",
    "No. ContractIQ points out clauses worth a second look and explains them in plain English. For high-stakes deals, take the marked-up review to a lawyer — it makes that conversation shorter.",
  ],
  ["Which files work?", "PDFs with selectable text, Word .docx files and plain .txt, up to 20 MB. Scanned images of pages have no text to read, so they can't be reviewed."],
  ["Who can see my contracts?", "Only your account. Contracts, reviews, obligations and alerts are tied to the account that uploaded them."],
  [
    "How accurate is the review?",
    "It's an AI review, so treat it as a careful first read rather than the last word. Every flag quotes the clause it's about, so you can check it against the contract in seconds.",
  ],
  ["Can I delete a contract?", "Yes. Deleting a contract removes its review, obligations and alerts with it."],
];

export default function Landing() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-30 border-b border-transparent bg-bg/85 backdrop-blur supports-[backdrop-filter]:bg-bg/70">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
          <Logo />
          <HomeActions compact />
        </div>
      </header>

      <main className="flex-1">
        {/* Hero, on faint legal-pad ruling */}
        <section className="legal-pad relative overflow-hidden">
          <div className="relative mx-auto grid max-w-6xl grid-cols-1 gap-14 px-4 pb-24 pt-10 sm:px-6 md:pt-16 lg:grid-cols-[minmax(0,25rem)_1fr] lg:items-center lg:gap-16">
            <div>
              <p className="inline-flex items-center gap-2 rounded-full border border-rule bg-page px-3 py-1 text-sm text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-mark-low" aria-hidden="true" />
                Reviews in about a minute
              </p>
              <h1 className="mt-5 text-[2.6rem] leading-[1.04] sm:text-6xl">Know what you&rsquo;re signing.</h1>
              <p className="mt-5 max-w-[42ch] text-lg text-muted">
                Upload a contract. ContractIQ highlights the clauses that could hurt you, explains each one in plain English, and keeps
                track of what you&rsquo;ve agreed to do.
              </p>
              <div className="mt-8">
                <HomeActions />
              </div>
              <ul className="mt-8 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted">
                <li className="flex items-center gap-2">
                  <span className="highlight highlight-high text-xs font-semibold">High</span> what to fix
                </li>
                <li className="flex items-center gap-2">
                  <span className="highlight highlight-medium text-xs font-semibold">Medium</span> what to watch
                </li>
                <li className="flex items-center gap-2">
                  <span className="highlight highlight-low text-xs font-semibold">Low</span> standard terms
                </li>
              </ul>
            </div>
            <MarkedPage />
          </div>
        </section>

        {/* What it catches */}
        <section aria-labelledby="catches" className="border-y border-rule bg-page">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <div className="grid gap-10 lg:grid-cols-[minmax(0,22rem)_1fr] lg:gap-16">
              <div>
                <h2 id="catches" className="text-3xl sm:text-4xl">
                  The clauses that cost people money
                </h2>
                <p className="mt-4 text-muted">
                  ContractIQ reads the whole agreement and flags clauses like these in the contract&rsquo;s own words, ranked by how much they could hurt.
                </p>
              </div>
              <ul className="grid gap-x-8 sm:grid-cols-2">
                {CATCHES.map(([k, t, d]) => (
                  <li key={t} className="border-t border-rule py-4">
                    <p className="font-serif text-lg">
                      <span className={`highlight highlight-${k}`}>{t}</span>
                    </p>
                    <p className="mt-1 text-sm text-muted">{d}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Product preview */}
        <section aria-labelledby="preview">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <div className="max-w-2xl">
              <h2 id="preview" className="text-3xl sm:text-4xl">
                A review you can act on
              </h2>
              <p className="mt-4 text-muted">
                A score for the whole contract, every flagged clause with a note beside it, and the obligations you&rsquo;re signing up for —
                on one page.
              </p>
            </div>
            <div className="mt-10">
              <ReviewPreview />
            </div>
          </div>
        </section>

        {/* Who it's for + how it works */}
        <section aria-labelledby="for" className="border-y border-rule bg-page">
          <div className="mx-auto grid max-w-6xl gap-16 px-4 py-20 sm:px-6 lg:grid-cols-2">
            <div>
              <h2 id="for" className="text-3xl">
                Made for people who sign without a legal team
              </h2>
              <dl className="mt-8 space-y-6">
                {FOR.map(([t, d]) => (
                  <div key={t} className="border-l-2 border-pen pl-4">
                    <dt className="font-semibold">{t}</dt>
                    <dd className="mt-1 text-muted">{d}</dd>
                  </div>
                ))}
              </dl>
            </div>
            <div>
              <h2 className="text-3xl">How it works</h2>
              <ol className="mt-8 space-y-6">
                {STEPS.map(([t, d], i) => (
                  <li key={t} className="flex gap-4">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-ink font-serif font-semibold">
                      {i + 1}
                    </span>
                    <div>
                      <p className="font-semibold">{t}</p>
                      <p className="mt-1 text-muted">{d}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section aria-labelledby="faq">
          <div className="mx-auto max-w-3xl px-4 py-20 sm:px-6">
            <h2 id="faq" className="text-3xl sm:text-4xl">
              Questions
            </h2>
            <div className="mt-8 divide-y divide-rule border-y border-rule">
              {FAQ.map(([q, a]) => (
                <details key={q} className="group py-1">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 py-4 font-semibold [&::-webkit-details-marker]:hidden">
                    {q}
                    <span aria-hidden="true" className="text-xl font-normal text-faint transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="max-w-[65ch] pb-5 text-muted">{a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* Closing call to action */}
        <section className="px-4 pb-20 sm:px-6">
          <div className="mx-auto max-w-6xl overflow-hidden rounded-2xl bg-[#161b2e] px-6 py-14 text-white sm:px-12">
            <div className="flex flex-col gap-8 md:flex-row md:items-center md:justify-between">
              <div>
                <h2 className="max-w-[22ch] text-3xl text-white sm:text-4xl">Read the next contract before you sign it.</h2>
                <p className="mt-3 max-w-[48ch] text-white/70">Upload it, read the mark-up, and walk into the negotiation knowing what to ask for.</p>
              </div>
              <Link href="/register" className="btn shrink-0 bg-[#fde98f] px-6 py-3.5 text-base text-[#3b2c00] hover:opacity-90">
                Review a contract
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SignatureFooter />
    </div>
  );
}