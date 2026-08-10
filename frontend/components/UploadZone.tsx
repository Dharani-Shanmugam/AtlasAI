"use client";

import { useCallback, useRef, useState } from "react";
import { CloudUpload, FileUp, Loader2, X } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import clsx from "clsx";

const ACCEPTED = ".pdf,.md,.markdown,.txt";

export function UploadZone({
  onUpload,
  onBatchUpload,
  disabled,
}: {
  onUpload: (file: File) => Promise<void>;
  onBatchUpload?: (files: File[]) => Promise<void>;
  disabled?: boolean;
}) {
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      setBusy(true);
      setError(null);
      try {
        if (files.length === 1) {
          await onUpload(files[0]);
        } else if (onBatchUpload) {
          await onBatchUpload(files);
        } else {
          for (const f of files) await onUpload(f);
        }
        setPendingFiles([]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setBusy(false);
      }
    },
    [onUpload, onBatchUpload]
  );

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          const files = Array.from(e.dataTransfer.files).filter((f) =>
            /\.(pdf|md|markdown|txt)$/i.test(f.name)
          );
          if (files.length > 0) {
            handleFiles(files);
          } else {
            setError("Only PDF, Markdown, and TXT files are supported.");
          }
        }}
        className={clsx(
          "relative flex cursor-pointer flex-col items-center justify-center gap-3 overflow-hidden rounded-2xl border-2 border-dashed px-6 py-14 text-center transition-all duration-300",
          dragging
            ? "border-violet-400/70 bg-violet-500/10 scale-[1.01]"
            : "border-white/15 bg-white/[0.02] hover:border-white/30 hover:bg-white/[0.04]"
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED}
          multiple
          disabled={busy || disabled}
          className="hidden"
          onChange={(e) => {
            const files = Array.from(e.target.files ?? []);
            if (files.length > 0) handleFiles(files);
            if (inputRef.current) inputRef.current.value = "";
          }}
        />
        <motion.div
          animate={busy ? { rotate: 360 } : { y: [0, -6, 0] }}
          transition={
            busy
              ? { repeat: Infinity, duration: 1, ease: "linear" }
              : { repeat: Infinity, duration: 2.5, ease: "easeInOut" }
          }
          className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-600 glow-ring"
        >
          {busy ? (
            <Loader2 className="h-7 w-7 text-white" />
          ) : (
            <CloudUpload className="h-7 w-7 text-white" />
          )}
        </motion.div>
        <div>
          <p className="text-base font-medium text-white">
            {busy ? "Indexing documents…" : "Drag & drop, or click to upload"}
          </p>
          <p className="mt-1 flex items-center justify-center gap-1.5 text-xs text-slate-500">
            <FileUp className="h-3.5 w-3.5" />
            PDF · Markdown · TXT — multiple files supported — up to 25 MB each
          </p>
        </div>

        {busy && (
          <div className="absolute inset-x-0 bottom-0 h-0.5 overflow-hidden">
            <motion.div
              className="h-full w-1/3 bg-gradient-to-r from-transparent via-violet-400 to-transparent"
              animate={{ x: ["-100%", "400%"] }}
              transition={{ repeat: Infinity, duration: 1.2, ease: "easeInOut" }}
            />
          </div>
        )}
      </div>

      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 flex items-center justify-between rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2"
          >
            <p className="text-xs text-red-300">{error}</p>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
              <X className="h-3.5 w-3.5" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
