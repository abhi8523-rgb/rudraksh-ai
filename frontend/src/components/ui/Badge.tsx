/* ════════════════════════════════════════════════════════════════
   Badge — Status badges
   ════════════════════════════════════════════════════════════════ */

type BadgeVariant = 'online' | 'offline' | 'processing' | 'error' | 'info' | 'warning' | 'default';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  dot?: boolean;
  className?: string;
  size?: 'sm' | 'md';
}

const variantClasses: Record<BadgeVariant, string> = {
  online: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  offline: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  processing: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  error: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
  info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  default: 'bg-white/5 text-gray-400 border-white/10',
};

const dotColors: Record<BadgeVariant, string> = {
  online: 'bg-emerald-400',
  offline: 'bg-gray-500',
  processing: 'bg-amber-400 animate-pulse',
  error: 'bg-rose-400',
  info: 'bg-blue-400',
  warning: 'bg-amber-400',
  default: 'bg-gray-400',
};

export default function Badge({ variant = 'default', children, dot = false, className = '', size = 'sm' }: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center gap-1.5
        font-medium rounded-full border
        ${size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-3 py-1 text-xs'}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${dotColors[variant]}`} />}
      {children}
    </span>
  );
}
