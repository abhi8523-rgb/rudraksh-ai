import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Outfit } from "next/font/google";
import "./globals.css";
import MainLayout from "@/components/layout/MainLayout";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });
const outfit = Outfit({ subsets: ["latin"], variable: "--font-outfit" });

export const metadata: Metadata = {
  title: "Rudraksh AI — Sovereign Intelligence Suite",
  description: "A privacy-first, locally-hosted AI platform with autonomous execution, modular industry verticals, and hardcoded governance.",
  keywords: ["AI", "LLM", "local", "privacy", "Ollama", "autonomous", "Rudraksh"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${jetbrainsMono.variable} ${outfit.variable} font-sans antialiased bg-[#0a0a1a] text-white`}>
        <MainLayout>{children}</MainLayout>
      </body>
    </html>
  );
}
