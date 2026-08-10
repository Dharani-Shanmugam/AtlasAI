"use client";

import { useMemo, useState } from "react";
import { ChevronDown, FileText } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import type { SourceRef } from "@/lib/types";

function SourceRow({ source }: { source: SourceRef }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      layout
      className="overflow-hidden rounded-lg border border-white/10 bg-white/[0.03]"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left transition-colors hover:bg-white/[0.05]"
      >
        <span className="flex min-w-0 items-center gap-2">
          <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 text-[10px] font-bold text-white">
            {source.number}
          </span>
          <span className="truncate text-xs text-slate-300">{source.filename}</span>
          <span className="hidden shrink-0 rounded bg-white/10 px-1.5 py-0.5 font-mono text-[10px] text-slate-400 sm:inline">
            chunk #{source.chunk_index + 1}
          </span>
        </span>
        <motion.span
          animate={{ rotate: open ? 180 : 0 }}
          className="shrink-0 text-slate-500"
        >
          <ChevronDown className="h-4 w-4" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
          >
            <p className="border-t border-white/10 px-3 py-2 text-xs leading-relaxed text-slate-400">
              {source.text}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export function CitationList({ sources }: { sources: SourceRef[] }) {
  const [open, setOpen] = useState(false);
  const files = useMemo(
    () => new Set(sources.map((s) => s.filename)),
    [sources]
  );

  if (sources.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="mt-4 border-t border-white/5 pt-3"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-2 text-xs font-medium text-slate-400 transition-colors hover:text-slate-200"
      >
        <FileText className="h-3.5 w-3.5" />
        {sources.length} source{sources.length > 1 ? "s" : ""}
        {files.size > 1 && ` · ${files.size} documents`}
        <motion.span animate={{ rotate: open ? 180 : 0 }}>
          <ChevronDown className="h-3.5 w-3.5" />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="mt-2 flex flex-col gap-1.5"
          >
            {sources.map((s) => (
              <SourceRow key={s.number} source={s} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
