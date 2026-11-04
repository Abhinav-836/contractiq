import { RISK, riskKey } from "@/lib/format";

const CHIP = {
  high: "bg-hi-high text-hi-high-ink",
  medium: "bg-hi-med text-hi-med-ink",
  low: "bg-hi-low text-hi-low-ink",
  not_contract: "bg-rule text-muted",
};

/** Risk shown as a highlighter swatch with its word — never colour alone. */
export function RiskChip({ level, short = false, className = "" }) {
  const k = riskKey(level);
  if (!k) return null;
  return (
    <span className={`highlight inline-block whitespace-nowrap text-[0.8125rem] font-semibold ${CHIP[k]} ${className}`}>
      {short ? RISK[k].short : RISK[k].label}
    </span>
  );
}

const BAR = { high: "bg-mark-high", medium: "bg-mark-med", low: "bg-mark-low" };

/** 0–100 score on the backend's bands (0–30 low, 31–60 medium, 61–100 high) with a pen-stroke marker. */
export function RiskMeter({ score, level }) {
  const s = Math.max(0, Math.min(100, Math.round(Number(score) || 0)));
  const k = riskKey(level) || (s >= 61 ? "high" : s >= 31 ? "medium" : "low");
  return (
    <div className="w-full sm:w-64">
      <div className="flex items-baseline justify-between">
        <span className="text-sm text-muted">Risk score</span>
        <RiskChip level={k} />
      </div>
      <p className="mt-1 font-serif text-5xl font-semibold leading-none">
        {s}
        <span className="ml-1 font-sans text-base font-normal text-muted">/ 100</span>
      </p>
      <div className="relative mt-3" role="img" aria-label={`Risk score ${s} out of 100, ${RISK[k].label.toLowerCase()}`}>
        <div className="flex h-1.5 overflow-hidden rounded-full">
          <span className="w-[30%] bg-hi-low" />
          <span className="w-[30%] bg-hi-med" />
          <span className="w-[40%] bg-hi-high" />
        </div>
        <span aria-hidden="true" className={`absolute -top-1 h-3.5 w-1 -translate-x-1/2 rounded-full ${BAR[k]}`} style={{ left: `${s}%` }} />
      </div>
    </div>
  );
}