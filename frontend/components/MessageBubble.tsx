"use client";

import { useEffect, useRef } from "react";
import { Bot, User } from "lucide-react";
import { motion } from "framer-motion";
import clsx from "clsx";
import { CitationList } from "@/components/CitationList";
import type { Message } from "@/lib/types";

function Markdown({ text }: { text: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    // Lightweight renderer: bold/italic/inline-code/links + paragraphs.
    const lines = text.split("\n");
    let html = "";
    let inList = false;
    const esc = (s: string) =>
      s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    const inline = (s: string) =>
      esc(s)
        .replace(/`([^`]+)`/g, '<code class="code">$1</code>')
        .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
        .replace(/\*([^*]+)\*/g, "<em>$1</em>");
    for (const line of lines) {
      if (/^[-•]\s+/.test(line)) {
        if (!inList) {
          html += '<ul class="mt-2 space-y-1">';
          inList = true;
        }
        html += `<li>${inline(line.replace(/^[-•]\s+/, ""))}</li>`;
      } else {
        if (inList) {
          html += "</ul>";
          inList = false;
        }
        if (line.trim() === "") html += "<p></p>";
        else html += `<p>${inline(line)}</p>`;
      }
    }
    if (inList) html += "</ul>";
    ref.current.innerHTML = html;
  }, [text]);

  return <div ref={ref} className="prose-p:mb-2" />;
}

export function MessageBubble({
  message,
  streaming,
}: {
  message: Message;
  streaming?: boolean;
}) {
  const isUser = message.role === "user";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: "spring", stiffness: 320, damping: 28 }}
      className={clsx("flex w-full gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={clsx(
          "mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border",
          isUser
            ? "border-white/10 bg-gradient-to-br from-cyan-500/30 to-violet-500/30"
            : "border-white/10 bg-gradient-to-br from-violet-500 to-fuchsia-600 glow-ring"
        )}
      >
        {isUser ? (
          <User className="h-4 w-4 text-cyan-200" />
        ) : (
          <Bot className="h-4 w-4 text-white" />
        )}
      </div>

      <div className={clsx("max-w-[85%] sm:max-w-[75%]", isUser && "text-right")}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.05 }}
          className={clsx(
            "rounded-2xl border px-4 py-3 text-[15px] leading-relaxed",
            isUser
              ? "rounded-tr-sm border-violet-400/20 bg-gradient-to-br from-violet-600/40 to-fuchsia-600/30 text-white"
              : "rounded-tl-sm glass text-slate-200"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <>
              <Markdown text={message.content} />
              {streaming && (
                <span className="ml-0.5 inline-block h-4 w-[7px] animate-blink rounded-sm bg-gradient-to-b from-violet-400 to-cyan-400 align-middle" />
              )}
            </>
          )}
        </motion.div>
        {!isUser && <CitationList sources={message.sources} />}
      </div>
    </motion.div>
  );
}
