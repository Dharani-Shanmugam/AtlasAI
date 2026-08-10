import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { Nav } from "@/components/Nav";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "AtlasAI — Chat with your documents",
  description:
    "Upload documents, then ask grounded questions with cited, streaming answers.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="font-sans">
        <AnimatedBackground />
        <Nav />
        <main className="relative z-10 min-h-screen pt-20">{children}</main>
      </body>
    </html>
  );
}
