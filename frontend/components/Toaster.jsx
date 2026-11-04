"use client";

import { removeToast, useToasts } from "@/lib/toast";

const TONE = { success: "border-l-ok", error: "border-l-danger", info: "border-l-pen" };

export default function Toaster() {
  const toasts = useToasts();
  return (
    <div aria-live="polite" className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(24rem,calc(100vw-2rem))] flex-col gap-2">
      {toasts.map((t) => (
        <div
          key={t.id}
          role={t.tone === "error" ? "alert" : "status"}
          className={`pointer-events-auto flex items-start gap-3 rounded-lg border border-rule border-l-4 bg-page px-4 py-3 text-sm shadow-lg shadow-black/10 ${TONE[t.tone] || TONE.info}`}
        >
          <p className="flex-1">{t.message}</p>
          <button type="button" onClick={() => removeToast(t.id)} aria-label="Dismiss" className="text-faint hover:text-ink">
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}