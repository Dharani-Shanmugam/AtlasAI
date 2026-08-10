"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { PanelLeftClose, PanelLeftOpen, Sparkles } from "lucide-react";
import { api, streamChat } from "@/lib/api";
import type { Message, SessionItem, SourceRef } from "@/lib/types";
import { MessageBubble } from "@/components/MessageBubble";
import { ChatInput } from "@/components/ChatInput";
import { SessionList } from "@/components/SessionList";

const SUGGESTIONS = [
  "What topics are covered in my documents?",
  "Summarize the key points",
  "Compare the main ideas across documents",
];

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions, setSessions] = useState<SessionItem[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const streamingRef = useRef(false);

  const refreshSessions = useCallback(async () => {
    try {
      setSessions(await api.sessions.list());
    } catch {
      /* backend may be down; keep stale list */
    }
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadSession = useCallback(
    async (id: string) => {
      if (streamingRef.current) return;
      setActiveId(id);
      setMessages(await api.sessions.messages(id));
    },
    []
  );

  const newChat = useCallback(() => {
    if (streamingRef.current) return;
    setActiveId(null);
    setMessages([]);
  }, []);

  const deleteSession = async (id: string) => {
    await api.sessions.remove(id);
    if (activeId === id) {
      setActiveId(null);
      setMessages([]);
    }
    refreshSessions();
  };

  const send = async (question: string) => {
    if (streamingRef.current) return;
    setError(null);

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      role: "user",
      content: question,
      sources: [],
      created_at: new Date().toISOString(),
    };
    const botMsg: Message = {
      id: `a-${Date.now()}`,
      role: "assistant",
      content: "",
      sources: [],
      created_at: new Date().toISOString(),
    };

    setMessages((m) => [...m, userMsg, botMsg]);
    setIsStreaming(true);
    streamingRef.current = true;

    try {
      await streamChat(question, activeId, (event) => {
        if (event.type === "meta") {
          setActiveId(event.session_id);
          setMessages((m) =>
            m.map((msg) =>
              msg.id === botMsg.id
                ? { ...msg, sources: event.citations as SourceRef[] }
                : msg
            )
          );
        } else if (event.type === "token") {
          setMessages((m) =>
            m.map((msg) =>
              msg.id === botMsg.id
                ? { ...msg, content: msg.content + event.content }
                : msg
            )
          );
        } else if (event.type === "error") {
          setError(event.message);
          setMessages((m) =>
            m.map((msg) =>
              msg.id === botMsg.id
                ? { ...msg, content: `⚠ ${event.message}` }
                : msg
            )
          );
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setIsStreaming(false);
      streamingRef.current = false;
      refreshSessions();
    }
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="mx-auto flex h-[calc(100dvh-5rem)] max-w-6xl gap-4 px-4 pb-4 sm:px-6">
      {/* Session sidebar */}
      <AnimatePresence initial={false}>
        {sidebarOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 260, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="hidden shrink-0 overflow-hidden sm:block"
          >
            <div className="h-full w-[260px]">
              <SessionList
                sessions={sessions}
                activeId={activeId}
                onSelect={loadSession}
                onNew={newChat}
                onDelete={deleteSession}
              />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      {/* Main chat */}
      <div className="flex min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 pb-3">
          <button
            onClick={() => setSidebarOpen((o) => !o)}
            className="glass glass-hover grid h-8 w-8 place-items-center rounded-lg text-slate-400"
            aria-label="Toggle sessions"
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </button>
          <h1 className="text-sm font-medium text-slate-400">
            {activeId
              ? sessions.find((s) => s.id === activeId)?.title ?? "Chat"
              : "New chat"}
          </h1>
          {error && (
            <span className="ml-auto truncate rounded-full border border-red-400/30 bg-red-500/10 px-3 py-1 text-xs text-red-300">
              {error}
            </span>
          )}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto pb-4">
          <AnimatePresence>
            {!hasMessages ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex h-full flex-col items-center justify-center text-center"
              >
                <motion.div
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                  className="mb-6 grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-600 glow-ring"
                >
                  <Sparkles className="h-8 w-8 text-white" />
                </motion.div>
                <h2 className="text-2xl font-semibold text-white">
                  Ask your <span className="text-gradient">documents</span> anything
                </h2>
                <p className="mt-2 max-w-md text-sm text-slate-400">
                  Upload a document first, then ask. Every answer is grounded in
                  your files and cites its sources.
                </p>
                <div className="mt-8 flex flex-wrap items-center justify-center gap-2">
                  {SUGGESTIONS.map((s, i) => (
                    <motion.button
                      key={s}
                      initial={{ opacity: 0, y: 12 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.15 + i * 0.1 }}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={() => send(s)}
                      className="glass glass-hover rounded-full px-4 py-2 text-sm text-slate-300"
                    >
                      {s}
                    </motion.button>
                  ))}
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="messages"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mx-auto flex max-w-3xl flex-col gap-6"
              >
                {messages.map((msg) => (
                  <MessageBubble
                    key={msg.id}
                    message={msg}
                    streaming={msg.id === messages.at(-1)?.id && isStreaming}
                  />
                ))}
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>

        <ChatInput disabled={isStreaming} onSubmit={send} />
      </div>
    </div>
  );
}
