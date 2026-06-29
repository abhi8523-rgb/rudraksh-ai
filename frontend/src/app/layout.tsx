import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import MainLayout from "@/components/layout/MainLayout";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "Neel AI — Sovereign Intelligence Suite",
  description: "A privacy-first, locally-hosted AI platform with autonomous execution, modular industry verticals, and hardcoded governance.",
  keywords: ["AI", "LLM", "local", "privacy", "Ollama", "autonomous", "Neel"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased bg-slate-50 text-slate-900`}>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
