import Link from "next/link";
import Logo from "@/components/Logo";
import MarkedPage from "@/components/MarkedPage";
import HomeActions from "@/components/HomeActions";

const FINDS = [
  {
    mark: "highlight-high",
    title: "Risky clauses, marked in place",
    body: "Liability caps, one-sided indemnities, termination traps and auto-renewals are highlighted in the contract's own words, with a plain-English note beside each.",
  },
  {
    mark: "highlight-medium",
    title: "What you've promised to do",
    body: "Payment terms, notice periods and reporting duties become a checklist of obligations you can tick off as you meet them.",
  },
  {
    mark: "highlight-low",
    title: "Dates and parties, pulled out",
    body: "Who signed, when it starts, how long it runs and when it renews — without reading all eleven pages.",
  },
];

const STEPS = [
  ["Upload the contract", "A text PDF, Word (.docx) or plain-text file, up to 20 MB."],
  ["Read the mark-up", "Each clause is scored low, medium or high risk, with what to ask for instead."],
  ["Keep track", "Obligations and alerts stay with the contract after you sign."],
];

export default function Landing() {
  return (
    <div className="flex min-h-dvh flex-col">
      <header className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5 sm:px-6">
        <Logo />
        <HomeActions compact />
      </header>

      <main className="flex-1">
        <section className="mx-auto grid max-w-6xl grid-cols-1 gap-12 px-4 pb-20 pt-8 sm:px-6 md:pt-14 lg:grid-cols-[minmax(0,25rem)_1fr] lg:items-center lg:gap-16">
          <div>
            <h1 className="text-[2.6rem] leading-[1.05] sm:text-6xl">Know what you&rsquo;re signing.</h1>
            <p className="mt-5 max-w-[42ch] text-lg text-muted">
              Upload a contract. ContractIQ highlights the clauses that could hurt you, explains each one in plain English, and keeps
              track of what you&rsquo;ve agreed to do.
            </p>
            <div className="mt-8">
              <HomeActions />
            </div>
            <p className="mt-4 text-sm text-faint">Your contracts are only visible to your account.</p>
          </div>
          <MarkedPage />
        </section>

        <section aria-labelledby="finds" className="border-t border-rule bg-page">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
            <h2 id="finds" className="text-3xl">
              What a review gives you
            </h2>
            <div className="mt-10 grid gap-10 md:grid-cols-3">
              {FINDS.map((f) => (
                <div key={f.title}>
                  <h3 className="font-sans text-base font-semibold tracking-normal">
                    <span className={`highlight ${f.mark}`}>{f.title}</span>
                  </h3>
                  <p className="mt-3 text-muted">{f.body}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section aria-labelledby="how" className="border-t border-rule">
          <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20">
            <h2 id="how" className="text-3xl">
              How it works
            </h2>
            <ol className="mt-10 grid gap-8 md:grid-cols-3">
              {STEPS.map(([title, body], i) => (
                <li key={title} className="border-t border-ink pt-4">
                  <p className="text-sm text-faint">Step {i + 1}</p>
                  <h3 className="mt-1 text-xl">{title}</h3>
                  <p className="mt-2 text-muted">{body}</p>
                </li>
              ))}
            </ol>
            <Link href="/register" className="btn btn-primary mt-12 px-5 py-3">
              Review your first contract
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t border-rule">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-6 text-sm text-faint sm:flex-row sm:justify-between sm:px-6">
          <p>ContractIQ flags risks to review. It isn&rsquo;t legal advice.</p>
          <p>
            Built by{" "}
            <a href="https://github.com/Abhinav-836" className="text-muted hover:text-ink">
              Abhinav Ashutosh
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}