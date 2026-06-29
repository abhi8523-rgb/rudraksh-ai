'use client';

import { useState } from 'react';
import Badge from '@/components/ui/Badge';
import { DEFAULT_MODELS } from '@/lib/constants';

/* Header — Clean top bar with model selector */

interface HeaderProps {
  currentModel?: string;
  onModelChange?: (model: string) => void;
}

export default function Header({ currentModel = 'llama3.2:3b', onModelChange }: HeaderProps) {
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const selectedModel = DEFAULT_MODELS.find((m) => m.id === currentModel) || DEFAULT_MODELS[0];

  return (
    <header className="flex items-center justify-between h-14 px-6 bg-white border-b border-slate-200">
      {/* Left: Status */}
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-emerald-500" />
        <span className="text-xs text-slate-500 font-medium">System Online</span>
      </div>

      {/* Right: Model Selector */}
      <div className="flex items-center gap-3">
        <div className="relative">
          <button
            onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <div className={`w-2 h-2 rounded-full ${selectedModel.isLoaded ? 'bg-emerald-500' : 'bg-slate-300'}`} />
            <span className="text-xs font-medium text-slate-700 max-w-[140px] truncate">
              {selectedModel.name}
            </span>
            <svg className="w-3 h-3 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {modelDropdownOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setModelDropdownOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-72 z-50 bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden">
                <div className="px-3 py-2 border-b border-slate-100">
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Available Models</span>
                </div>
                {DEFAULT_MODELS.map((model) => (
                  <button
                    key={model.id}
                    onClick={() => {
                      onModelChange?.(model.id);
                      setModelDropdownOpen(false);
                    }}
                    className={`flex items-center gap-3 w-full px-3 py-2.5 hover:bg-slate-50 transition-colors text-left ${
                      currentModel === model.id ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className={`w-2 h-2 rounded-full flex-shrink-0 ${model.isLoaded ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-slate-800 truncate">{model.name}</div>
                      <div className="text-[10px] text-slate-400">{model.provider} · {model.parameters}</div>
                    </div>
                    <Badge variant={model.isLoaded ? 'online' : 'offline'} size="sm">
                      {model.isLoaded ? 'Ready' : 'Idle'}
                    </Badge>
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
