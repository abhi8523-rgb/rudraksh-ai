'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MODULES } from '@/lib/constants';

/* ════════════════════════════════════════════════════════════════
   ModuleNav — Segmented module navigation bar
   
   Shows all modules as a segmented control / tab bar with:
   - Color-coded segments per module
   - Active indicator with gradient glow
   - Dropdown for smaller screens
   ════════════════════════════════════════════════════════════════ */

export default function ModuleNav() {
  const pathname = usePathname();
  const [showDropdown, setShowDropdown] = useState(false);

  const activeModule = MODULES.find((m) =>
    m.path === '/' ? pathname === '/' : pathname.startsWith(m.path)
  );

  return (
    <>
      {/* Desktop: Segmented control */}
      <div className="hidden md:flex items-center gap-1 p-1 mx-6 mt-4 rounded-2xl bg-white/[0.03] border border-white/[0.06] overflow-x-auto scrollbar-thin">
        {MODULES.map((mod) => {
          const active = mod.path === '/' ? pathname === '/' : pathname.startsWith(mod.path);
          return (
            <Link key={mod.id} href={mod.path} className="flex-shrink-0">
              <motion.div
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all cursor-pointer ${
                  active
                    ? 'text-white shadow-lg'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {active && (
                  <motion.div
                    layoutId="module-active-bg"
                    className={`absolute inset-0 rounded-xl bg-gradient-to-r ${mod.gradient} opacity-20`}
                    transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                  />
                )}
                <span className="relative z-10">{mod.icon}</span>
                <span className="relative z-10 hidden lg:inline">{mod.name}</span>
              </motion.div>
            </Link>
          );
        })}
      </div>

      {/* Mobile: Dropdown selector */}
      <div className="md:hidden mx-4 mt-4 relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="w-full flex items-center justify-between gap-3 px-4 py-3 rounded-2xl bg-white/[0.04] border border-white/[0.08] text-white"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg">{activeModule?.icon || '🔱'}</span>
            <span className="font-medium">{activeModule?.name || 'Select Module'}</span>
          </div>
          <motion.svg
            animate={{ rotate: showDropdown ? 180 : 0 }}
            className="w-5 h-5 text-gray-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </motion.svg>
        </button>

        <AnimatePresence>
          {showDropdown && (
            <motion.div
              initial={{ opacity: 0, y: -10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              className="absolute top-full left-0 right-0 mt-2 z-50 rounded-2xl bg-[#12121f] border border-white/[0.08] shadow-xl overflow-hidden"
            >
              {MODULES.map((mod) => {
                const active = mod.path === '/' ? pathname === '/' : pathname.startsWith(mod.path);
                return (
                  <Link key={mod.id} href={mod.path} onClick={() => setShowDropdown(false)}>
                    <div
                      className={`flex items-center gap-3 px-4 py-3 text-sm transition-all ${
                        active
                          ? 'bg-white/[0.06] text-white'
                          : 'text-gray-400 hover:bg-white/[0.03] hover:text-white'
                      }`}
                    >
                      <span className="text-lg">{mod.icon}</span>
                      <div>
                        <div className="font-medium">{mod.name}</div>
                        <div className="text-xs text-gray-600">{mod.description}</div>
                      </div>
                      {active && (
                        <div className={`ml-auto w-2 h-2 rounded-full bg-gradient-to-r ${mod.gradient}`} />
                      )}
                    </div>
                  </Link>
                );
              })}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
