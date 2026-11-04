import Link from "next/link";

export function Spinner({ className = "h-4 w-4" }) {
  return <span aria-hidden="true" className={`inline-block animate-spin rounded-full border-2 border-current border-r-transparent ${className}`} />;
}

export function Loading({ label = "Loading…" }) {
  return (
    <p role="status" className="flex items-center gap-2 py-10 text-muted">
      <Spinner /> {label}
    </p>
  );
}

export function ErrorNote({ message, onRetry }) {
  return (
    <div role="alert" className="rounded-lg border border-danger/30 bg-danger/5 px-4 py-3 text-danger">
      {message}{" "}
      {onRetry && (
        <button type="button" onClick={onRetry} className="font-semibold underline underline-offset-4">
          Try again
        </button>
      )}
    </div>
  );
}

export function Empty({ title, body, action, href }) {
  return (
    <div className="rounded-xl border border-dashed border-rule bg-page px-6 py-12 text-center">
      <p className="font-serif text-lg font-semibold">{title}</p>
      {body && <p className="mx-auto mt-1 max-w-[46ch] text-muted">{body}</p>}
      {action && href && (
        <Link href={href} className="btn btn-primary mt-5">
          {action}
        </Link>
      )}
    </div>
  );
}

export function PageHead({ title, sub, children }) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-3xl sm:text-4xl">{title}</h1>
        {sub && <p className="mt-2 text-muted">{sub}</p>}
      </div>
      {children && <div className="flex shrink-0 flex-wrap gap-2">{children}</div>}
    </div>
  );
}

/** Segmented filter used on list pages. */
export function Filters({ value, onChange, options, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="flex gap-1 overflow-x-auto rounded-lg border border-rule bg-page p-1 text-sm">
      {options.map(([v, l, count]) => (
        <button
          key={v}
          type="button"
          role="radio"
          aria-checked={value === v}
          onClick={() => onChange(v)}
          className={`shrink-0 rounded-md px-3 py-1.5 transition-colors ${value === v ? "bg-ink font-medium text-page" : "text-muted hover:text-ink"}`}
        >
          {l}
          {count != null && <span className={`ml-1.5 tabular-nums ${value === v ? "opacity-70" : "text-faint"}`}>{count}</span>}
        </button>
      ))}
    </div>
  );
}