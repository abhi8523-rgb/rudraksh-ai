/* Badge — Light theme status badges */

type BadgeVariant = 'online' | 'offline' | 'processing' | 'error' | 'info' | 'warning' | 'default';

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  dot?: boolean;
  className?: string;
  size?: 'sm' | 'md';
}

const variantClasses: Record<BadgeVariant, string> = {
  online: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  offline: 'bg-slate-50 text-slate-500 border-slate-200',
  processing: 'bg-amber-50 text-amber-700 border-amber-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  info: 'bg-blue-50 text-blue-700 border-blue-200',
  warning: 'bg-amber-50 text-amber-700 border-amber-200',
  default: 'bg-slate-50 text-slate-600 border-slate-200',
};

const dotColors: Record<BadgeVariant, string> = {
  online: 'bg-emerald-500',
  offline: 'bg-slate-400',
  processing: 'bg-amber-500 animate-pulse',
  error: 'bg-red-500',
  info: 'bg-blue-500',
  warning: 'bg-amber-500',
  default: 'bg-slate-400',
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
