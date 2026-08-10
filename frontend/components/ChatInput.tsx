"use client";

import { useRef, useState } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export function ChatInput({
  disabled,
  onSubmit,
}: {
  disabled?: boolean;
  onSubmit: (text: string) => void;
}) {
  const [value, setValue] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  const canSend = value.trim().length > 0 && !disabled;

  const submit = () => {
    if (!canSend) return;
    onSubmit(value.trim());
    setValue("");
    if (ref.current) ref.current.style.height = "auto";
  };

  return (
    <motion.div
      initial={{ y: 20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, delay: 0.1 }}
      className="mx-auto w-full max-w-3xl"
    >
      <div className="glass glow-ring flex items-end gap-2 rounded-2xl p-2 focus-within:border-violet-400/40">
        <textarea
          ref={ref}
          rows={1}
          value={value}
          disabled={disabled}
          onChange={(e) => {
            setValue(e.target.value);
            const el = e.target;
            el.style.height = "auto";
            el.style.height = Math.min(el.scrollHeight, 160) + "px";
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
          placeholder="Ask anything about your documents…"
          className="max-h-40 flex-1 resize-none bg-transparent px-3 py-2 text-[15px] text-white placeholder:text-slate-500 focus:outline-none disabled:opacity-50"
        />
        <motion.button
          whileHover={canSend ? { scale: 1.05 } : undefined}
          whileTap={canSend ? { scale: 0.92 } : undefined}
          onClick={submit}
          disabled={!canSend}
          aria-label="Send message"
          className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 text-white transition-opacity disabled:opacity-30"
        >
          {disabled ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <ArrowUp className="h-5 w-5" />
          )}
        </motion.button>
      </div>
      <p className="mt-2 text-center text-[11px] text-slate-600">
        Answers are grounded only in your uploaded documents · Enter to send, Shift+Enter for a new line
      </p>
    </motion.div>
  );
}
