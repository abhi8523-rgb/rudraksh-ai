'use client';

import { useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

/* MainLayout — Fixed sidebar + scrollable content */

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [currentModel, setCurrentModel] = useState('llama3.2:3b');

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      {/* Fixed Sidebar */}
      <Sidebar />

      {/* Main Content — takes remaining width */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header currentModel={currentModel} onModelChange={setCurrentModel} />

        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
