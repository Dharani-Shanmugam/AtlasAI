"use client";

import Link from "next/link";
import {
  ArrowRight,
  FileSearch,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: MessageCircle,
    title: "Streaming answers",
    desc: "Responses stream in token-by-token with a live cursor — feel the model think.",
  },
  {
    icon: FileSearch,
    title: "Cited, grounded responses",
    desc: "Every claim links back to the exact chunk it came from. No hallucinations, no guesswork.",
  },
  {
    icon: Zap,
    title: "Instant indexing",
    desc: "Upload a PDF or Markdown and it's chunked, embedded, and searchable in seconds.",
  },
  {
    icon: ShieldCheck,
    title: "Your data, your rules",
    desc: "Local embeddings and optional local models. Full control over where your documents live.",
  },
];

const steps = [
  { n: "01", label: "Upload", desc: "PDF · Markdown · TXT" },
  { n: "02", label: "Index", desc: "Chunked + embedded" },
  { n: "03", label: "Ask", desc: "Grounded, cited answers" },
];

export default function HomePage() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
      {/* Hero */}
      <div className="flex flex-col items-center text-center">
        <motion.span
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass mb-6 inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs text-slate-300"
        >
          <Sparkles className="h-3.5 w-3.5 text-violet-400" />
          Retrieval-Augmented Generation, production-grade
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.05 }}
          className="max-w-3xl text-5xl font-bold leading-[1.1] tracking-tight text-white sm:text-6xl"
        >
          Chat with your{" "}
          <span className="text-gradient">documents</span>.
          <br />
          Get cited, grounded answers.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
          className="mt-6 max-w-xl text-base text-slate-400"
        >
          AtlasAI turns your files into a private knowledge base. Upload, ask, and
          every answer points back to the source — built to be read, understood,
          and extended.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.25 }}
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            href="/chat"
            className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-6 py-3 text-sm font-semibold text-white transition-all hover:scale-[1.03] glow-ring"
          >
            Start chatting
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            href="/documents"
            className="glass glass-hover inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-slate-200"
          >
            Upload documents
          </Link>
        </motion.div>

        {/* Steps */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.35 }}
          className="mt-16 flex w-full max-w-xl items-center justify-between gap-2"
        >
          {steps.map((s, i) => (
            <div key={s.n} className="flex flex-1 items-center gap-2">
              <div className="flex flex-1 flex-col items-center text-center">
                <span className="text-gradient font-mono text-sm font-bold">{s.n}</span>
                <span className="mt-1 text-sm font-semibold text-white">{s.label}</span>
                <span className="mt-0.5 text-xs text-slate-500">{s.desc}</span>
              </div>
              {i < steps.length - 1 && (
                <motion.div
                  animate={{ x: [0, 6, 0] }}
                  transition={{ repeat: Infinity, duration: 2, delay: i * 0.3 }}
                  className="mb-4 h-px flex-1 bg-gradient-to-r from-violet-500/50 to-cyan-400/50"
                />
              )}
            </div>
          ))}
        </motion.div>
      </div>

      {/* Features */}
      <motion.div
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-80px" }}
        variants={{ visible: { transition: { staggerChildren: 0.08 } } }}
        className="mt-24 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {features.map(({ icon: Icon, title, desc }) => (
          <motion.div
            key={title}
            variants={{
              hidden: { opacity: 0, y: 24 },
              visible: { opacity: 1, y: 0 },
            }}
            transition={{ type: "spring", stiffness: 280, damping: 24 }}
            whileHover={{ y: -6 }}
            className="glass glass-hover group rounded-2xl p-5"
          >
            <div className="mb-4 grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-violet-500/30 to-cyan-500/30 transition-transform group-hover:scale-110">
              <Icon className="h-5 w-5 text-violet-200" />
            </div>
            <h3 className="text-sm font-semibold text-white">{title}</h3>
            <p className="mt-2 text-xs leading-relaxed text-slate-400">{desc}</p>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
