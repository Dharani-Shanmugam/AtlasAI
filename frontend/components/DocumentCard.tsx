"use client";

import { useState } from "react";
import {
  FileText,
  File as FileIcon,
  Loader2,
  Sparkles,
  Trash2,
} from "lucide-react";
import { motion } from "framer-motion";
import type { DocumentItem } from "@/lib/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const STATUS_STYLES: Record<DocumentItem["status"], string> = {
  ready: "border-emerald-400/30 bg-emerald-500/10 text-emerald-300",
  pending: "border-amber-400/30 bg-amber-500/10 text-amber-300",
  failed: "border-red-400/30 bg-red-500/10 text-red-300",
};

export function DocumentCard({
  doc,
  onDelete,
  onExtractTopics,
  topicBusy,
  topicCount,
}: {
  doc: DocumentItem;
  onDelete: (id: string) => void;
  onExtractTopics?: () => void;
  topicBusy?: boolean;
  topicCount?: number;
}) {
  const isPdf = doc.content_type === "application/pdf";
  const isPending = doc.status === "pending";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.92, y: 12 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ type: "spring", stiffness: 300, damping: 26 }}
      whileHover={{ y: -4 }}
      className="glass glass-hover group relative flex flex-col gap-3 overflow-hidden rounded-2xl p-4"
    >
      <div className="flex items-start justify-between gap-3">
        <div
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-xl ${
            isPdf
              ? "bg-gradient-to-br from-red-500/40 to-orange-500/30"
              : "bg-gradient-to-br from-cyan-500/40 to-violet-500/30"
          }`}
        >
          {isPdf ? (
            <FileText className="h-5 w-5 text-red-200" />
          ) : (
            <FileIcon className="h-5 w-5 text-cyan-200" />
          )}
        </div>
        <span
          className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium capitalize ${STATUS_STYLES[doc.status]}`}
        >
          {isPending && <Loader2 className="h-3 w-3 animate-spin" />}
          {doc.status}
        </span>
      </div>

      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-white" title={doc.filename}>
          {doc.filename}
        </p>
        <p className="mt-1 text-xs text-slate-500">
          {formatBytes(doc.file_size)} ·{" "}
          {doc.status === "ready"
            ? `${doc.chunk_count} chunks indexed`
            : doc.status === "failed"
              ? doc.error ?? "failed to index"
              : "indexing…"}
        </p>
      </div>

      {doc.status === "ready" && (
        <div className="mt-1">
          <div className="flex justify-between text-[10px] text-slate-600">
            <span>indexed</span>
            <span>{doc.chunk_count}</span>
          </div>
          <div className="mt-1 h-1 overflow-hidden rounded-full bg-white/5">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 0.8, delay: 0.2, ease: "easeOut" }}
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-cyan-400"
            />
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {onExtractTopics && (
          <button
            onClick={onExtractTopics}
            disabled={topicBusy}
            className="mt-1 flex items-center gap-1.5 rounded-lg bg-violet-500/10 px-2.5 py-1.5 text-[11px] text-violet-300 transition-colors hover:bg-violet-500/20 disabled:opacity-50"
          >
            {topicBusy ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Sparkles className="h-3 w-3" />
            )}
            {topicCount && topicCount > 0
              ? `${topicCount} topics`
              : "Extract topics"}
          </button>
        )}
      </div>

      <button
        onClick={() => onDelete(doc.id)}
        aria-label="Delete document"
        className="absolute right-3 top-3 -translate-y-1 translate-x-1 rounded-lg p-1.5 text-slate-500 opacity-0 transition-all hover:bg-red-500/10 hover:text-red-400 group-hover:translate-x-0 group-hover:opacity-100"
      >
        <Trash2 className="h-4 w-4" />
      </button>
    </motion.div>
  );
}
