import { RISK, riskKey } from "@/lib/format";

const MARK = { high: "bg-mark-high", medium: "bg-mark-med", low: "bg-mark-low" };
const NOTE_EDGE = { high: "border-l-mark-high", medium: "border-l-mark-med", low: "border-l-mark-low" };

/**
 * One clause as a marked-up document: the contract wording on the left with a
 * highlighter wash by risk, and the reviewer's margin comment on the right —
 * what it means and what to ask for instead. Stacks on narrow screens.
 */
export function Clause({ clause, index }) {
  const k = riskKey(clause.risk_level) || "medium";
  const text = (clause.clause_text || "").trim();
  return (
    <li className="grid gap-x-8 gap-y-3 py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,19rem)]">
      <div className="min-w-0">
        <p className="flex items-baseline gap-2 text-sm text-muted">
          <span className="tabular-nums text-faint">§{index + 1}</span>
          <span className="font-semibold text-ink">{clause.clause_type || "Clause"}</span>
        </p>
        {text ? (
          <p className="mt-2 font-serif text-[1.0625rem] leading-8">
            <span className={`highlight highlight-${k}`}>{text}</span>
          </p>
        ) : (
          <p className="mt-2 text-muted">The clause wording wasn&rsquo;t captured for this item.</p>
        )}
      </div>

      <aside
        aria-label={`Review note for ${clause.clause_type || "clause"}`}
        className={`relative self-start rounded-r-lg border-l-[3px] bg-page py-3 pl-4 pr-4 shadow-sm shadow-black/5 md:mt-7 ${NOTE_EDGE[k]}`}
      >
        {/* connector from the highlighted text to the note, like a Word comment */}
        <span aria-hidden="true" className={`absolute -left-8 top-5 hidden h-px w-[calc(2rem-3px)] md:block ${MARK[k]} opacity-60`} />
        <p className="text-sm font-semibold">{RISK[k].label}</p>
        {clause.explanation && <p className="mt-1 text-sm text-muted">{clause.explanation}</p>}
        {clause.recommendation && (
          <p className="mt-2 text-sm">
            <span className="font-semibold">Ask for: </span>
            {clause.recommendation}
          </p>
        )}
      </aside>
    </li>
  );
}

const ORDER = { high: 0, medium: 1, low: 2 };

export default function ClauseReview({ clauses, filter = "all" }) {
  const list = (clauses || [])
    .map((c, i) => ({ c, i }))
    .filter(({ c }) => filter === "all" || (riskKey(c.risk_level) || "medium") === filter)
    .sort((a, b) => (ORDER[riskKey(a.c.risk_level)] ?? 1) - (ORDER[riskKey(b.c.risk_level)] ?? 1) || a.i - b.i);

  if (!list.length) {
    return <p className="py-8 text-muted">No clauses at this risk level.</p>;
  }
  return (
    <ol className="divide-y divide-rule">
      {list.map(({ c, i }) => (
        <Clause key={i} clause={c} index={i} />
      ))}
    </ol>
  );
}