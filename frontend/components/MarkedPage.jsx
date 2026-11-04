/*
 * Landing-page specimen: a page of a services agreement as ContractIQ marks it
 * up. Static markup — it shows the product rather than describing it.
 */
const NOTES = [
  {
    k: "high",
    top: "lg:top-[3.5rem]",
    title: "High risk",
    body: "Their liability stops at 3 months of fees. Yours has no limit.",
    ask: "a mutual cap at 12 months of fees.",
  },
  {
    k: "medium",
    top: "lg:top-[15rem]",
    title: "Medium risk",
    body: "Renews for a year unless you cancel 90 days before the end.",
    ask: "a 30-day notice window instead.",
  },
];

const EDGE = { high: "border-l-mark-high", medium: "border-l-mark-med" };

export default function MarkedPage() {
  return (
    <figure aria-label="A contract page marked up by ContractIQ" className="relative mx-auto w-full max-w-[34rem] lg:max-w-none">
      <div className="rounded-lg border border-rule bg-page px-6 py-7 shadow-xl shadow-black/[0.07] sm:px-8 lg:mr-64">
        <p className="text-xs text-faint">Master Services Agreement · page 3 of 11</p>
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
      </div>

      {/* margin notes: beside the page on wide screens, below it on narrow ones */}
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:mt-0 lg:block">
        {NOTES.map((n) => (
          <aside
            key={n.k}
            className={`rounded-r-lg border-l-[3px] bg-page px-4 py-3 text-sm shadow-lg shadow-black/[0.07] lg:absolute lg:right-0 lg:w-56 lg:before:absolute lg:before:-left-8 lg:before:top-5 lg:before:h-px lg:before:w-8 lg:before:bg-current lg:before:opacity-30 ${n.top} ${EDGE[n.k]}`}
          >
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