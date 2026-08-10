"use client";

import { useCallback, useEffect, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Boxes,
  FileStack,
  Globe,
  Inbox,
  Link2,
  Loader2,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";
import type { DocumentItem, TopicItem } from "@/lib/types";
import { UploadZone } from "@/components/UploadZone";
import { DocumentCard } from "@/components/DocumentCard";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [urlInput, setUrlInput] = useState("");
  const [urlBusy, setUrlBusy] = useState(false);
  const [urlError, setUrlError] = useState<string | null>(null);
  const [topics, setTopics] = useState<TopicItem[]>([]);
  const [topicBusyDocId, setTopicBusyDocId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const res = await api.documents.list();
      setDocuments(res.documents);
      if (res.documents.some((d) => d.status === "pending")) {
        setTimeout(refresh, 1500);
      }
    } catch {
      /* backend down */
    }
    try {
      const t = await api.topics.list();
      setTopics(t.topics);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const upload = async (file: File) => {
    setBusy(true);
    try {
      await api.documents.upload(file);
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  const batchUpload = async (files: File[]) => {
    setBusy(true);
    try {
      await api.documents.batchUpload(files);
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  const remove = async (id: string) => {
    setDocuments((docs) => docs.filter((d) => d.id !== id));
    await api.documents.remove(id);
    refresh();
  };

  const ingestUrl = async () => {
    if (!urlInput.trim()) return;
    setUrlBusy(true);
    setUrlError(null);
    try {
      await api.documents.ingestUrl(urlInput.trim());
      setUrlInput("");
      await refresh();
    } catch (err) {
      setUrlError(err instanceof Error ? err.message : "Failed to ingest URL");
    } finally {
      setUrlBusy(false);
    }
  };

  const extractTopics = async (docId: string) => {
    setTopicBusyDocId(docId);
    try {
      await api.topics.extract(docId);
      const t = await api.topics.list();
      setTopics(t.topics);
    } catch (err) {
      console.error(err);
    } finally {
      setTopicBusyDocId(null);
    }
  };

  const ready = documents.filter((d) => d.status === "ready").length;
  const totalChunks = documents
    .filter((d) => d.status === "ready")
    .reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mb-8"
      >
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Your <span className="text-gradient">knowledge base</span>
        </h1>
        <p className="mt-2 max-w-xl text-sm text-slate-400">
          Upload files or paste a URL — AtlasAI indexes them into searchable
          chunks, then you can ask questions with cited answers.
        </p>
      </motion.div>

      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Left: Upload + URL input */}
        <div className="space-y-4">
          <UploadZone onUpload={upload} onBatchUpload={batchUpload} disabled={busy} />

          {/* URL ingestion */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="glass rounded-2xl p-4"
          >
            <div className="flex items-center gap-2 mb-3">
              <Globe className="h-4 w-4 text-cyan-300" />
              <span className="text-sm font-medium text-white">Ingest from URL</span>
            </div>
            <div className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && ingestUrl()}
                placeholder="https://example.com/article"
                className="flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-cyan-400/50 focus:outline-none"
              />
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.96 }}
                onClick={ingestUrl}
                disabled={urlBusy || !urlInput.trim()}
                className="flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-violet-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
              >
                {urlBusy ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Link2 className="h-4 w-4" />
                )}
                Fetch
              </motion.button>
            </div>
            {urlError && (
              <p className="mt-2 text-xs text-red-400">{urlError}</p>
            )}
          </motion.div>
        </div>

        {/* Right: Stats */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="grid grid-cols-2 gap-3"
        >
          {[
            { icon: FileStack, label: "Documents", value: ready },
            { icon: Boxes, label: "Chunks indexed", value: totalChunks },
            { icon: Sparkles, label: "Topics found", value: topics.length },
          ].map(({ icon: Icon, label, value }) => (
            <div
              key={label}
              className="glass glass-hover flex flex-col items-start gap-2 rounded-2xl p-4"
            >
              <Icon className="h-5 w-5 text-violet-300" />
              <span className="text-3xl font-bold text-white">{value}</span>
              <span className="text-xs text-slate-500">{label}</span>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Document list */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15 }}
        className="mt-10"
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
            All documents
          </h2>
          <span className="text-xs text-slate-600">{documents.length} total</span>
        </div>

        {documents.length === 0 ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass flex flex-col items-center gap-3 rounded-2xl border-dashed py-16 text-center"
          >
            <Inbox className="h-10 w-10 text-slate-600" />
            <p className="text-sm text-slate-500">
              Nothing here yet — upload your first document above.
            </p>
          </motion.div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence mode="popLayout">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  onDelete={remove}
                  onExtractTopics={
                    doc.status === "ready" ? () => extractTopics(doc.id) : undefined
                  }
                  topicBusy={topicBusyDocId === doc.id}
                  topicCount={
                    topics.filter((t) => t.doc_id === doc.id).length
                  }
                />
              ))}
            </AnimatePresence>
          </div>
        )}
      </motion.div>

      {/* Topic map */}
      {topics.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-10"
        >
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-500">
            Topic map
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <AnimatePresence mode="popLayout">
              {topics.map((topic) => (
                <motion.div
                  key={topic.id}
                  layout
                  initial={{ opacity: 0, scale: 0.92 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  whileHover={{ y: -4 }}
                  className="glass glass-hover rounded-2xl p-4"
                >
                  <h3 className="text-sm font-semibold text-white">
                    {topic.name}
                  </h3>
                  <p className="mt-1 text-xs text-slate-400 leading-relaxed">
                    {topic.summary}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1">
                    {topic.keywords.map((kw) => (
                      <span
                        key={kw}
                        className="rounded-full bg-violet-500/15 px-2 py-0.5 text-[10px] text-violet-300"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                  <p className="mt-2 text-[10px] text-slate-600">
                    {topic.chunk_indices.length} relevant chunks
                  </p>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </motion.div>
      )}
    </div>
  );
}
