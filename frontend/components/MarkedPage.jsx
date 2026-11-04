/*
 * Landing-page specimen: page 3 of a services agreement as ContractIQ marks
 * it up, sitting on the rest of the stack, with the score card clipped on.
 * Static markup — it shows the product rather than describing it.
 */
const NOTES = [
  {
    k: "high",
    top: "lg:top-[4.25rem]",
    title: "High risk",
    body: "Their liability stops at 3 months of fees. Yours has no limit.",
    ask: "a mutual cap at 12 months of fees.",
  },
  {
    k: "medium",
    top: "lg:top-[16rem]",
    title: "Medium risk",
    body: "Renews for a year unless you cancel 90 days before the end.",
    ask: "a 30-day notice window instead.",
  },
];

const EDGE = { high: "border-l-mark-high", medium: "border-l-mark-med" };
const LINE = { high: "bg-mark-high", medium: "bg-mark-med" };

function ScoreCard() {
  return (
    <div className="absolute -bottom-8 left-4 z-20 w-56 rounded-lg border border-rule bg-page p-4 shadow-xl shadow-black/10 sm:-left-6">
      <div className="flex items-baseline justify-between">
        <span className="text-xs text-muted">Risk score</span>
        <span className="highlight highlight-high text-xs font-semibold">High risk</span>
      </div>
      <p className="mt-1 font-serif text-4xl font-semibold leading-none">
        78<span className="ml-1 font-sans text-sm font-normal text-muted">/ 100</span>
      </p>
      <div className="relative mt-2.5">
        <div className="flex h-1.5 overflow-hidden rounded-full">
          <span className="w-[30%] bg-hi-low" />
          <span className="w-[30%] bg-hi-med" />
          <span className="w-[40%] bg-hi-high" />
        </div>
        <span className="absolute -top-1 left-[78%] h-3.5 w-1 -translate-x-1/2 rounded-full bg-mark-high" />
      </div>
      <p className="mt-3 text-xs text-muted">3 high, 2 medium, 2 low clauses</p>
    </div>
  );
}

export default function MarkedPage() {
  return (
    <figure aria-label="A contract page marked up by ContractIQ" className="relative mx-auto w-full max-w-[34rem] pb-10 lg:max-w-none">
      <div className="relative lg:mr-64">
        {/* the rest of the contract, fanned out behind */}
        <div aria-hidden="true" className="absolute inset-0 translate-x-3 translate-y-3 rotate-[2.2deg] rounded-lg border border-rule bg-page/80 shadow-md shadow-black/5" />
        <div aria-hidden="true" className="absolute inset-0 translate-x-1.5 translate-y-1.5 rotate-[1deg] rounded-lg border border-rule bg-page shadow-md shadow-black/5" />

        <div className="relative rounded-lg border border-rule bg-page px-6 pb-16 pt-7 shadow-xl shadow-black/[0.08] sm:px-8">
          <div className="flex items-baseline justify-between text-xs text-faint">
            <span>Master Services Agreement</span>
            <span className="tabular-nums">3 / 11</span>
          </div>
          <div className="mt-4 space-y-4 font-serif text-[0.95rem] leading-7 text-ink/85">
            <p>
              <span className="font-semibold text-ink">3. Limitation of Liability.</span>{" "}
              <span className="highlight highlight-high">
                Vendor&rsquo;s total liability shall not exceed the fees paid in the three (3) months preceding the claim. Client&rsquo;s
                liability shall be unlimited.
              </span>
            </p>
            <p>
              <span className="font-semibold text-ink">4. Confidentiality.</span> Each party shall keep the other&rsquo;s confidential
              information secret for five (5) years after termination.
            </p>
            <p>
              <span className="font-semibold text-ink">5. Term.</span>{" "}
              <span className="highlight highlight-medium">
                This Agreement renews automatically for successive twelve (12) month terms unless either party gives ninety (90) days&rsquo;
                written notice.
              </span>
            </p>
            <p>
              <span className="font-semibold text-ink">6. Governing Law.</span>{" "}
              <span className="highlight highlight-low">Laws of India, courts of Bengaluru.</span>
            </p>
          </div>
          {/* the rest of the page, out of focus */}
          <div aria-hidden="true" className="mt-5 space-y-2.5">
            {[96, 88, 92, 60].map((w, i) => (
              <div key={i} className="h-2 rounded-full bg-rule/70" style={{ width: `${w}%` }} />
            ))}
          </div>
        </div>
        <ScoreCard />
      </div>

      {/* margin notes: beside the page on wide screens, below it on narrow ones */}
      <div className="mt-14 grid gap-3 sm:grid-cols-2 lg:mt-0 lg:block">
        {NOTES.map((n) => (
          <aside
            key={n.k}
            className={`relative rounded-r-lg border-l-[3px] bg-page px-4 py-3 text-sm shadow-lg shadow-black/[0.07] lg:absolute lg:right-0 lg:w-56 ${n.top} ${EDGE[n.k]}`}
          >
            <span aria-hidden="true" className={`absolute -left-9 top-5 hidden h-px w-8 opacity-50 lg:block ${LINE[n.k]}`} />
            <p className="font-semibold">{n.title}</p>
            <p className="mt-0.5 text-muted">{n.body}</p>
            <p className="mt-1.5">
              <span className="font-semibold">Ask for: </span>
              {n.ask}
            </p>
          </aside>
        ))}
      </div>
    </figure>
  );
}