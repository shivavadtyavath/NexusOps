import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NexusOps — Autonomous DevOps Intelligence Platform",
  description:
    "AI-powered code review, bug detection, security scanning, and automated fix generation. Built with Groq, LangGraph, PyGithub, and bandit. 100% free stack.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#0d1117] text-white h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}
