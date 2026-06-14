'use client';

import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

/* ════════════════════════════════════════════════════════════════
   Card — Glassmorphism card with hover glow
   ════════════════════════════════════════════════════════════════ */

interface CardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  glow?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

const paddingClasses = {
  none: '',
  sm: 'p-3',
  md: 'p-5',
  lg: 'p-7',
};

export default function Card({
  children,
  className = '',
  hover = true,
  glow = false,
  padding = 'md',
  onClick,
}: CardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      whileHover={hover ? { y: -2, transition: { duration: 0.2 } } : undefined}
      onClick={onClick}
      className={`
        relative overflow-hidden
        bg-white/[0.03] backdrop-blur-xl
        border border-white/[0.06]
        rounded-xl
        transition-all duration-300
        ${hover ? 'hover:bg-white/[0.05] hover:border-white/[0.1] hover:shadow-lg hover:shadow-black/20' : ''}
        ${glow ? 'hover:shadow-[0_0_30px_rgba(59,130,246,0.12)]' : ''}
        ${paddingClasses[padding]}
        ${onClick ? 'cursor-pointer' : ''}
        ${className}
      `}
    >
      {glow && (
        <div className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none bg-gradient-to-br from-blue-500/[0.03] to-indigo-500/[0.03]" />
      )}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}
