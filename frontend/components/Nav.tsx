"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, FileText, Settings } from "lucide-react";
import { motion } from "framer-motion";
import clsx from "clsx";

const links = [
  { href: "/chat", label: "Chat", icon: Sparkles },
  { href: "/documents", label: "Documents", icon: FileText },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <motion.header
      initial={{ y: -24, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed inset-x-0 top-0 z-40"
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 glow-ring">
            <Sparkles className="h-5 w-5 text-white" />
          </span>
          <span className="text-lg font-semibold tracking-tight text-white">
            Atlas<span className="text-gradient">AI</span>
          </span>
        </Link>

        <nav className="glass flex items-center gap-1 rounded-full p-1">
          {links.map(({ href, label, icon: Icon }) => {
            const active = pathname === href || pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "relative rounded-full px-4 py-1.5 text-sm font-medium transition-colors",
                  active ? "text-white" : "text-slate-400 hover:text-slate-200"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 rounded-full bg-gradient-to-r from-violet-600 to-fuchsia-600"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }}
                  />
                )}
                <span className="relative z-10 flex items-center gap-1.5">
                  <Icon className="h-4 w-4" />
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>
      </div>
    </motion.header>
  );
}
