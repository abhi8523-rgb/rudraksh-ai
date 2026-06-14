'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Badge from '@/components/ui/Badge';
import { DEFAULT_MODELS } from '@/lib/constants';

/* ════════════════════════════════════════════════════════════════
   Header — Top bar with status, model selector, controls
   ════════════════════════════════════════════════════════════════ */

interface HeaderProps {
  currentModel?: string;
  onModelChange?: (model: string) => void;
}

export default function Header({ currentModel = 'deepseek-r1:14b', onModelChange }: HeaderProps) {
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const selectedModel = DEFAULT_MODELS.find((m) => m.id === currentModel) || DEFAULT_MODELS[0];

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between h-16 px-6
      bg-[#0a0a1a]/60 backdrop-blur-2xl border-b border-white/[0.06]">
      {/* Left: Breadcrumb / Title area */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs text-gray-500 font-medium">System Online</span>
        </div>
      </div>

      {/* Center: Search */}
      <div className="flex-1 max-w-lg mx-8">
        <AnimatePresence>
          {searchOpen ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative"
            >
              <input
                autoFocus
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search across modules..."
                className="w-full px-4 py-2 pl-10
                  bg-white/[0.04] border border-white/[0.08]
                  rounded-xl text-sm text-white placeholder-gray-600
                  focus:outline-none focus:border-blue-500/30 focus:bg-white/[0.06]
                  transition-all duration-200"
                onBlur={() => { setSearchOpen(false); setSearchQuery(''); }}
              />
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </motion.div>
          ) : (
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              onClick={() => setSearchOpen(true)}
              className="flex items-center gap-2 px-4 py-2 w-full
                bg-white/[0.02] border border-white/[0.06] rounded-xl
                text-gray-600 text-sm hover:bg-white/[0.04] hover:border-white/[0.1]
                transition-all duration-200"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span>Search...</span>
              <kbd className="ml-auto px-1.5 py-0.5 text-[10px] bg-white/5 border border-white/10 rounded text-gray-600">⌘K</kbd>
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Right: Model Selector + Controls */}
      <div className="flex items-center gap-3">
        {/* Model Selector */}
        <div className="relative">
          <button
            onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5
              bg-white/[0.04] border border-white/[0.08]
              rounded-lg hover:bg-white/[0.06] hover:border-white/[0.12]
              transition-all duration-200"
          >
            <div className={`w-2 h-2 rounded-full ${selectedModel.isLoaded ? 'bg-emerald-400' : 'bg-gray-600'}`} />
            <span className="text-xs font-medium text-gray-300 max-w-[120px] truncate">
              {selectedModel.name}
            </span>
            <svg className="w-3 h-3 text-gray-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <AnimatePresence>
            {modelDropdownOpen && (
              <motion.div
                initial={{ opacity: 0, y: -8, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.96 }}
                transition={{ duration: 0.15 }}
                className="absolute right-0 top-full mt-2 w-72
                  bg-[#0f0f23]/95 backdrop-blur-2xl
                  border border-white/[0.08] rounded-xl
                  shadow-2xl shadow-black/40 overflow-hidden"
              >
                <div className="px-3 py-2 border-b border-white/[0.06]">
                  <span className="text-[10px] font-semibold text-gray-600 uppercase tracking-wider">Available Models</span>
                </div>
                {DEFAULT_MODELS.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => {
                      onModelChange?.(model.id);
                      setModelDropdownOpen(false);
                    }}
                    className={`flex items-center gap-3 w-full px-3 py-2.5
                      hover:bg-white/[0.04] transition-colors
                      ${currentModel === model.id ? 'bg-blue-500/5' : ''}`}
                  >
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${model.isLoaded ? 'bg-emerald-400' : 'bg-gray-600'}`} />
                    <div className="flex-1 text-left min-w-0">
                      <div className="text-xs font-medium text-gray-300 truncate">{model.name}</div>
                      <div className="text-[10px] text-gray-600">{model.provider} · {model.parameters}</div>
                    </div>
                    <Badge variant={model.isLoaded ? 'online' : 'offline'} size="sm">
                      {model.isLoaded ? 'Loaded' : 'Idle'}
                    </Badge>
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Divider */}
        <div className="w-px h-6 bg-white/[0.06]" />

        {/* Notification Bell */}
        <button className="relative p-2 text-gray-500 hover:text-white hover:bg-white/[0.05] rounded-lg transition-all duration-200">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-blue-500" />
        </button>

        {/* Settings */}
        <button className="p-2 text-gray-500 hover:text-white hover:bg-white/[0.05] rounded-lg transition-all duration-200">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>
    </header>
  );
}
