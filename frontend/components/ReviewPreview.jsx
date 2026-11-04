import { Clause } from "./ClauseReview";
import { RiskMeter } from "./Risk";

/*
 * The real contract-review components rendered with a sample agreement,
 * inside a browser frame — what a user actually gets after uploading.
 */
const SAMPLE = [
  {
    clause_type: "Indemnification",
    risk_level: "high",
    clause_text:
      "Client shall indemnify Vendor against all third-party claims arising from use of the services, including claims caused by Vendor's negligence.",
    explanation: "You would pay for claims the vendor caused. Indemnities are normally limited to each party's own fault.",
    recommendation: "Mutual indemnities that exclude the other party's negligence.",
  },
  {
    clause_type: "Payment",
    risk_level: "medium",
    clause_text: "Client shall pay each invoice within 45 days of receipt. Late payments accrue interest at 2% per month.",
    explanation: "2% a month is about 27% a year, well above typical late-payment rates.",
    recommendation: "Interest capped at 1% per month, starting after a written reminder.",
  },
];

const OBLIGATIONS = [
  ["Pay each invoice within 45 days", "Recurring"],
  ["Send renewal notice", "By 30 Nov 2027"],
  ["Report data breaches within 72 hours", "When it happens"],
];

export default function ReviewPreview() {
  return (
    <div className="overflow-hidden rounded-xl border border-rule bg-bg shadow-2xl shadow-black/10">
      <div className="flex items-center gap-2 border-b border-rule bg-page px-4 py-2.5" aria-hidden="true">
        <span className="h-2.5 w-2.5 rounded-full bg-rule" />
        <span className="h-2.5 w-2.5 rounded-full bg-rule" />
        <span className="h-2.5 w-2.5 rounded-full bg-rule" />
        <span className="ml-3 truncate rounded-md bg-bg px-3 py-1 text-xs text-faint">contractiq · Brightline MSA 2026.pdf</span>
      </div>

      <div className="pointer-events-none select-none p-5 sm:p-8" inert="">
        <div className="flex flex-col gap-6 border-b border-rule pb-6 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0">
            <p className="font-serif text-2xl font-semibold sm:text-3xl">Brightline MSA 2026.pdf</p>
            <p className="mt-1 text-sm text-muted">PDF, 11 pages, reviewed in 41 seconds</p>
          </div>
          <RiskMeter score={78} level="high" />
        </div>

        <div className="mt-6 grid gap-8 lg:grid-cols-[minmax(0,1fr)_15rem]">
          <div className="min-w-0">
            <p className="max-w-[62ch] font-serif text-lg leading-relaxed">
              A two-year services deal that leans toward the vendor: you indemnify them even for their own negligence, and late payments
              cost far more than usual.
            </p>
            <ol className="mt-2 divide-y divide-rule">
              {SAMPLE.map((c, i) => (
                <Clause key={c.clause_type} clause={c} index={i} />
              ))}
            </ol>
          </div>
          <div className="space-y-3 lg:border-l lg:border-rule lg:pl-6">
            <p className="text-sm font-semibold text-muted">Obligations</p>
            {OBLIGATIONS.map(([t, d]) => (
              <div key={t} className="flex gap-2.5 text-sm">
                <span className="mt-1 h-3.5 w-3.5 shrink-0 rounded-[3px] border border-faint" aria-hidden="true" />
                <div>
                  <p>{t}</p>
                  <p className="text-faint">{d}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}