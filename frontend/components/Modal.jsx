"use client";

import { useEffect, useRef } from "react";

// Native <dialog>: focus trap, Esc and backdrop for free.
export default function Modal({ open, onClose, title, children }) {
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (open && !el.open) el.showModal();
    if (!open && el.open) el.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(e) => e.target === ref.current && onClose()}
      className="m-auto w-[calc(100vw-2rem)] max-w-md rounded-xl border border-rule bg-page p-0 text-ink shadow-2xl backdrop:bg-ink/40"
    >
      {open && (
        <div className="p-6">
          <h2 className="text-xl">{title}</h2>
          <div className="mt-3">{children}</div>
        </div>
      )}
    </dialog>
  );
}

export function ConfirmDelete({ open, onClose, onConfirm, busy, title, body, confirmLabel = "Delete" }) {
  return (
    <Modal open={open} onClose={() => !busy && onClose()} title={title}>
      <p className="text-muted">{body}</p>
      <div className="mt-6 flex justify-end gap-2">
        <button type="button" className="btn btn-quiet" onClick={onClose} disabled={busy}>
          Keep it
        </button>
        <button type="button" className="btn btn-danger" onClick={onConfirm} disabled={busy}>
          {busy ? "Deleting…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}