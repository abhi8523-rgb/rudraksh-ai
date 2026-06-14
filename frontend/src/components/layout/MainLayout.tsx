'use client';

import { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';
import ModuleNav from './ModuleNav';

/* ════════════════════════════════════════════════════════════════
   MainLayout — Wrapper combining sidebar + header + module nav + content
   ════════════════════════════════════════════════════════════════ */

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [currentModel, setCurrentModel] = useState('deepseek-r1:14b');

  return (
    <div className="min-h-screen bg-bg-primary mesh-gradient noise-overlay">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="pl-[72px] lg:pl-[260px] transition-all duration-300">
        <Header currentModel={currentModel} onModelChange={setCurrentModel} />
        
        {/* Segmented Module Navigation */}
        <ModuleNav />

        <main className="relative min-h-[calc(100vh-64px)]">
          {children}
        </main>
      </div>
    </div>
  );
}
