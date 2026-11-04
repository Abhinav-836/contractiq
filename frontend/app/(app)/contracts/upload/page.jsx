"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useUploadContract } from "@/lib/queries";
import { errorMessage } from "@/lib/api";
import { fileSize } from "@/lib/format";
import { track } from "@/lib/track";
import { toast } from "@/lib/toast";
import { Spinner } from "@/components/States";

const MAX_BYTES = 20 * 1024 * 1024;
const ALLOWED = [".pdf", ".docx", ".txt"];

function check(file) {
  const ext = file.name.includes(".") ? `.${file.name.split(".").pop().toLowerCase()}` : "";
  if (ext === ".doc") return "Old .doc files can't be read. Save it as .docx or PDF and upload that.";
  if (!ALLOWED.includes(ext)) return "Use a PDF, Word (.docx) or plain-text (.txt) file.";
  if (file.size === 0) return "That file is empty.";
  if (file.size > MAX_BYTES) return `That file is ${fileSize(file.size)}. The limit is 20 MB.`;
  return "";
}

export default function UploadPage() {
  const router = useRouter();
  const upload = useUploadContract();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);

  const pick = (f) => {
    if (!f) return;
    const problem = check(f);
    setError(problem);
    setFile(problem ? null : f);
  };

  const submit = (e) => {
    e.preventDefault();
    if (!file) return setError("Choose a file first.");
    setProgress(0);
    upload.mutate(
      { file, onProgress: setProgress },
      {
        onSuccess: (res) => {
          track("contract_uploaded", { type: file.name.split(".").pop().toLowerCase() });
          toast("Uploaded. The review has started.", "success");
          router.push(`/contracts/${res.id}`);
        },
        onError: (err) => setError(errorMessage(err, "The upload failed.")),
      },
    );
  };

  const busy = upload.isPending;

  return (
    <div className="mx-auto max-w-2xl">
      <Link href="/contracts" className="text-sm text-muted hover:text-ink">
        Contracts
      </Link>
      <h1 className="mt-2 text-3xl sm:text-4xl">Upload a contract</h1>
      <p className="mt-2 text-muted">The review usually takes under a minute. You can leave this page while it runs.</p>

      <form onSubmit={submit} className="mt-8">
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            if (!busy) pick(e.dataTransfer.files?.[0]);
          }}
          className={`flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors ${
            dragging ? "border-pen bg-pen/5" : file ? "border-pen/50 bg-page" : "border-rule bg-page hover:border-faint"
          } ${busy ? "pointer-events-none opacity-70" : ""}`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.txt"
            className="sr-only"
            disabled={busy}
            onChange={(e) => {
              pick(e.target.files?.[0]);
              e.target.value = ""; // allow picking the same file again after an error
            }}
          />
          {file ? (
            <>
              <span className="font-serif text-lg font-semibold break-all">{file.name}</span>
              <span className="mt-1 text-sm text-muted">{fileSize(file.size)}</span>
              {!busy && <span className="mt-3 text-sm text-pen">Choose a different file</span>}
            </>
          ) : (
            <>
              <span className="font-serif text-lg font-semibold">Drop the contract here</span>
              <span className="mt-1 text-muted">
                or <span className="font-semibold text-pen">browse your files</span>
              </span>
              <span className="mt-4 text-sm text-faint">PDF with selectable text, Word (.docx) or .txt, up to 20 MB</span>
            </>
          )}
        </label>

        {busy && (
          <div className="mt-4" role="status">
            <div className="flex justify-between text-sm text-muted">
              <span>{progress < 100 ? "Uploading…" : "Starting the review…"}</span>
              <span className="tabular-nums">{progress}%</span>
            </div>
            <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-rule">
              <div className="h-full rounded-full bg-pen transition-[width]" style={{ width: `${progress}%` }} />
            </div>
          </div>
        )}

        {error && (
          <p role="alert" className="mt-4 rounded-lg border border-danger/30 bg-danger/5 px-3 py-2.5 text-sm text-danger">
            {error}
          </p>
        )}

        <div className="mt-6 flex flex-wrap justify-end gap-2">
          <Link href="/contracts" className={`btn btn-quiet ${busy ? "pointer-events-none opacity-50" : ""}`}>
            Cancel
          </Link>
          <button type="submit" className="btn btn-primary" disabled={!file || busy}>
            {busy && <Spinner />}
            {busy ? "Uploading…" : "Upload and review"}
          </button>
        </div>
      </form>

      <p className="mt-10 border-t border-rule pt-5 text-sm text-faint">
        Scanned PDFs (photos of pages) have no text to read, so the review will fail. Export the original document instead.
      </p>
    </div>
  );
}