"use client";

import { AnimatePresence, motion } from "framer-motion";
import { MessageSquare, Plus, Trash2 } from "lucide-react";
import clsx from "clsx";
import type { SessionItem } from "@/lib/types";

export function SessionList({
  sessions,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: {
  sessions: SessionItem[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="glass flex h-full flex-col rounded-2xl p-3">
      <button
        onClick={onNew}
        className="mb-3 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-3 py-2.5 text-sm font-medium text-white transition-transform hover:scale-[1.02] active:scale-[0.98]"
      >
        <Plus className="h-4 w-4" /> New chat
      </button>

      <div className="flex-1 space-y-1 overflow-y-auto">
        <AnimatePresence initial={false}>
          {sessions.map((s) => (
            <motion.div
              key={s.id}
              layout
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              transition={{ duration: 0.2 }}
              className={clsx(
                "group flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2.5 text-sm transition-colors",
                s.id === activeId
                  ? "bg-white/[0.08] text-white"
                  : "text-slate-400 hover:bg-white/[0.04] hover:text-slate-200"
              )}
              onClick={() => onSelect(s.id)}
            >
              <MessageSquare className="h-3.5 w-3.5 shrink-0 opacity-60" />
              <span className="flex-1 truncate">{s.title}</span>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(s.id);
                }}
                className="opacity-0 transition-opacity group-hover:opacity-100 hover:text-red-400"
                aria-label="Delete session"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
        {sessions.length === 0 && (
          <p className="px-3 py-6 text-center text-xs text-slate-600">
            No conversations yet
          </p>
        )}
      </div>
    </div>
  );
}
