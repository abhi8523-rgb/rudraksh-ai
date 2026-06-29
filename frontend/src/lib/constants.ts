import type { ModuleConfig, SidebarItem } from '@/types';

/* ════════════════════════════════════════════════════════════════
   Neel AI — Constants
   ════════════════════════════════════════════════════════════════ */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const APP_NAME = 'Neel AI';
export const APP_TAGLINE = 'Your Sovereign Intelligence Suite';
export const APP_VERSION = '1.0.0';

// ── Module Configurations ──
export const MODULES: ModuleConfig[] = [
  {
    id: 'chat',
    name: 'Chat',
    description: 'Intelligent conversations with any loaded model',
    icon: '💬',
    path: '/',
    color: '#3b82f6',
    gradient: 'from-blue-500 to-indigo-500',
  },
  {
    id: 'coders',
    name: 'Coders',
    description: 'Code generation, analysis & debugging tools',
    icon: '⚡',
    path: '/coders',
    color: '#8b5cf6',
    gradient: 'from-violet-500 to-purple-500',
  },
  {
    id: 'social-media',
    name: 'Social Media',
    description: 'Content planning, drafting & scheduling',
    icon: '📱',
    path: '/social-media',
    color: '#ec4899',
    gradient: 'from-pink-500 to-rose-500',
  },
  {
    id: 'marketing',
    name: 'Marketing',
    description: 'Campaign strategy, SEO & analytics',
    icon: '📊',
    path: '/marketing',
    color: '#f59e0b',
    gradient: 'from-amber-500 to-orange-500',
  },
  {
    id: 'students',
    name: 'Students',
    description: 'Study tools, tutoring & learning assistant',
    icon: '🎓',
    path: '/students',
    color: '#10b981',
    gradient: 'from-emerald-500 to-teal-500',
  },
  {
    id: 'research',
    name: 'Research',
    description: 'RAG-powered deep research & analysis',
    icon: '🔬',
    path: '/research',
    color: '#06b6d4',
    gradient: 'from-cyan-500 to-blue-500',
  },
  {
    id: 'trident',
    name: 'Trident',
    description: 'Autonomous execution engine with DAG visualization',
    icon: '🔱',
    path: '/trident',
    color: '#f97316',
    gradient: 'from-orange-500 to-red-500',
  },
  {
    id: 'sovereign',
    name: 'Sovereign',
    description: 'Admin dashboard & system management',
    icon: '👑',
    path: '/sovereign',
    color: '#eab308',
    gradient: 'from-yellow-500 to-amber-500',
  },
];

// ── Sidebar Navigation ──
export const SIDEBAR_ITEMS: SidebarItem[] = [
  { id: 'chat', label: 'Chat', icon: '💬', path: '/' },
  { id: 'coders', label: 'Coders', icon: '⚡', path: '/coders' },
  { id: 'social', label: 'Social Media', icon: '📱', path: '/social-media' },
  { id: 'marketing', label: 'Marketing', icon: '📊', path: '/marketing' },
  { id: 'students', label: 'Students', icon: '🎓', path: '/students' },
  { id: 'research', label: 'Research', icon: '🔬', path: '/research' },
  { id: 'trident', label: 'Trident', icon: '🔱', path: '/trident' },
  { id: 'sovereign', label: 'Sovereign', icon: '👑', path: '/sovereign' },
];

// ── Default Models ──
export const DEFAULT_MODELS = [
  { id: 'llama3.2:3b', name: 'Llama 3.2 3B', provider: 'Ollama', contextLength: 131072, isLoaded: true, parameters: '3B' },
  { id: 'deepseek-r1:14b', name: 'DeepSeek R1 14B', provider: 'Ollama', contextLength: 32768, isLoaded: false, parameters: '14B' },
  { id: 'llama3.1:8b', name: 'Llama 3.1 8B', provider: 'Ollama', contextLength: 131072, isLoaded: false, parameters: '8B' },
  { id: 'mistral:7b', name: 'Mistral 7B', provider: 'Ollama', contextLength: 32768, isLoaded: false, parameters: '7B' },
];

// ── Status Colors ──
export const STATUS_COLORS = {
  online: '#10b981',
  offline: '#6b7280',
  processing: '#f59e0b',
  error: '#f43f5e',
} as const;

// ── Chart Colors ──
export const CHART_COLORS = [
  '#3b82f6',
  '#6366f1',
  '#8b5cf6',
  '#ec4899',
  '#f59e0b',
  '#10b981',
  '#06b6d4',
  '#f97316',
];
