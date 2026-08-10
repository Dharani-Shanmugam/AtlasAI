"use client";

import { motion } from "framer-motion";

const blobs = [
  {
    color: "rgba(139,92,246,0.35)",
    size: "32rem",
    top: "-10%",
    left: "-5%",
    duration: 18,
  },
  {
    color: "rgba(217,70,239,0.22)",
    size: "26rem",
    top: "20%",
    right: "-8%",
    duration: 22,
  },
  {
    color: "rgba(34,211,238,0.18)",
    size: "24rem",
    bottom: "-12%",
    left: "30%",
    duration: 26,
  },
];

export function AnimatedBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 overflow-hidden">
      {/* subtle grid */}
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
        }}
      />
      {blobs.map((b, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-[120px]"
          style={{
            width: b.size,
            height: b.size,
            background: `radial-gradient(circle, ${b.color}, transparent 70%)`,
            top: b.top,
            left: b.left,
            right: b.right,
            bottom: b.bottom,
          }}
          animate={{ x: [0, 40, -20, 0], y: [0, -30, 20, 0], scale: [1, 1.08, 0.95, 1] }}
          transition={{ duration: b.duration, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
      {/* vignette to keep edges dark */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,#050510_100%)]" />
    </div>
  );
}
