import Link from "next/link";

const SEG = {
  high: { label: "High risk", bar: "bg-mark-high", chip: "highlight-high" },
  medium: { label: "Medium", bar: "bg-mark-med", chip: "highlight-medium" },
  low: { label: "Low", bar: "bg-mark-low", chip: "highlight-low" },
  other: { label: "Reviewing or failed", bar: "bg-rule", chip: "" },
};

/**
 * Proportional bar of how many items sit at each risk level, with a legend
 * that carries the counts (so the bar never relies on colour alone).
 * `hrefFor(key)` makes legend entries links; omit for plain text.
 */
export default function RiskBar({ counts, hrefFor, label = "Risk breakdown", compact = false }) {
  const keys = ["high", "medium", "low", "other"].filter((k) => counts[k] > 0);
  const total = keys.reduce((n, k) => n + counts[k], 0);
  if (!total) return null;

  return (
    <div>
      <div
        className={`flex w-full gap-0.5 overflow-hidden rounded-full ${compact ? "h-2" : "h-3"}`}
        role="img"
        aria-label={`${label}: ${keys.map((k) => `${counts[k]} ${SEG[k].label.toLowerCase()}`).join(", ")}`}
      >
        {keys.map((k) => (
          <span key={k} className={SEG[k].bar} style={{ width: `${(counts[k] / total) * 100}%` }} />
        ))}
      </div>
      <ul className={`flex flex-wrap gap-x-5 gap-y-1.5 ${compact ? "mt-2 text-xs" : "mt-3 text-sm"}`}>
        {keys.map((k) => {
          const body = (
            <>
              <span aria-hidden="true" className={`inline-block h-2 w-2 rounded-full ${SEG[k].bar}`} />
              <span className="tabular-nums font-semibold text-ink">{counts[k]}</span>
              <span className="text-muted">{SEG[k].label}</span>
            </>
          );
          const href = hrefFor?.(k);
          return (
            <li key={k}>
              {href ? (
                <Link href={href} className="flex items-center gap-1.5 hover:underline">
                  {body}
                </Link>
              ) : (
                <span className="flex items-center gap-1.5">{body}</span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}