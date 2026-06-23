'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { SIDEBAR_ITEMS, APP_NAME } from '@/lib/constants';

/* ════════════════════════════════════════════════════════════════
   Sidebar — Collapsible navigation with icon+label modes
   ════════════════════════════════════════════════════════════════ */

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const isActive = (path: string) => {
    if (path === '/') return pathname === '/';
    return pathname.startsWith(path);
  };

  return (
    <motion.aside
      initial={false}
      animate={{ width: collapsed ? 72 : 260 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      className="fixed left-0 top-0 bottom-0 z-40 flex flex-col
        bg-[#0a0a1a]/80 backdrop-blur-2xl
        border-r border-white/[0.06]"
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-white/[0.06]">
        <Link href="/" className="flex items-center gap-3 min-w-0">
          <div className="relative flex-shrink-0 w-9 h-9">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 animate-glow-pulse" />
            <div className="relative flex items-center justify-center w-full h-full rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600">
              <span className="text-lg font-bold text-white">N</span>
            </div>
          </div>
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                transition={{ duration: 0.2 }}
                className="flex flex-col min-w-0"
              >
                <span className="text-sm font-bold text-white tracking-tight truncate">{APP_NAME}</span>
                <span className="text-[10px] text-gray-500 tracking-wider uppercase">Intelligence Suite</span>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-thin">
        <div className="mb-3 px-3">
          <AnimatePresence>
            {!collapsed && (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest"
              >
                Modules
              </motion.span>
            )}
          </AnimatePresence>
        </div>

        {SIDEBAR_ITEMS.map((item) => {
          const active = isActive(item.path);
          return (
            <Link key={item.id} href={item.path}>
              <motion.div
                whileHover={{ x: 2 }}
                whileTap={{ scale: 0.98 }}
                className={`
                  relative flex items-center gap-3 px-3 py-2.5 rounded-xl
                  transition-all duration-200 group cursor-pointer
                  ${active
                    ? 'bg-gradient-to-r from-blue-500/10 to-indigo-500/10 text-white'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.03]'
                  }
                `}
              >
                {/* Active indicator */}
                {active && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-6 rounded-full bg-gradient-to-b from-blue-400 to-indigo-500"
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}

                {/* Icon */}
                <span className={`text-lg flex-shrink-0 ${collapsed ? 'mx-auto' : ''}`}>
                  {item.icon}
                </span>

                {/* Label */}
                <AnimatePresence>
                  {!collapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -8 }}
                      transition={{ duration: 0.15 }}
                      className="text-sm font-medium truncate"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {/* Hover glow for active */}
                {active && (
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </motion.div>
            </Link>
          );
        })}
      </nav>

      {/* Collapse Toggle */}
      <div className="px-3 py-3 border-t border-white/[0.06]">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center w-full p-2 rounded-xl
            text-gray-500 hover:text-white hover:bg-white/[0.05]
            transition-all duration-200"
        >
          <motion.svg
            animate={{ rotate: collapsed ? 180 : 0 }}
            transition={{ duration: 0.3 }}
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
          </motion.svg>
        </button>
      </div>
    </motion.aside>
  );
}
