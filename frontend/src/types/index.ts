/* ════════════════════════════════════════════════════════════════
   Neel AI — TypeScript Interfaces & Types
   ════════════════════════════════════════════════════════════════ */

// ── Chat ──
export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  model?: string;
  tokens?: number;
  isStreaming?: boolean;
  attachments?: Attachment[];
}

export interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  model: string;
  module: ModuleType;
  createdAt: number;
  updatedAt: number;
}

// ── Models ──
export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  contextLength: number;
  isLoaded: boolean;
  parameters?: string;
}

// ── Modules ──
export type ModuleType =
  | 'chat'
  | 'coders'
  | 'social-media'
  | 'marketing'
  | 'students'
  | 'research'
  | 'trident'
  | 'sovereign';

export interface ModuleConfig {
  id: ModuleType;
  name: string;
  description: string;
  icon: string;
  path: string;
  color: string;
  gradient: string;
}

// ── Trident ──
export interface TaskNode {
  id: string;
  label: string;
  type: 'goal' | 'plan' | 'action' | 'tool' | 'result';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  dependencies: string[];
  output?: string;
  duration?: number;
  x?: number;
  y?: number;
}

export interface ExecutionStep {
  id: string;
  timestamp: number;
  type: 'thought' | 'action' | 'observation' | 'result' | 'error';
  content: string;
  metadata?: Record<string, unknown>;
}

export interface DAGExecution {
  id: string;
  goal: string;
  nodes: TaskNode[];
  steps: ExecutionStep[];
  status: 'idle' | 'planning' | 'executing' | 'completed' | 'failed';
  startedAt?: number;
  completedAt?: number;
}

// ── Sovereign ──
export interface SystemHealth {
  cpu: number;
  memory: number;
  disk: number;
  uptime: number;
  modelsLoaded: number;
  totalModels: number;
  gpuUsage?: number;
  gpuTemp?: number;
}

export interface UsageMetric {
  date: string;
  requests: number;
  tokens: number;
  avgLatency: number;
}

export interface AuditEntry {
  id: string;
  timestamp: number;
  action: string;
  module: string;
  user: string;
  details: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// ── Documents ──
export interface Document {
  id: string;
  name: string;
  type: string;
  size: number;
  status: 'uploading' | 'processing' | 'indexed' | 'error';
  progress?: number;
  uploadedAt: number;
  chunks?: number;
}

// ── API ──
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface StreamEvent {
  type: 'token' | 'done' | 'error' | 'metadata';
  content?: string;
  metadata?: Record<string, unknown>;
}

// ── Auth ──
export interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  expiresAt: number | null;
}

// ── Sidebar ──
export interface SidebarItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: string;
  children?: SidebarItem[];
}

// ── Notifications ──
export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: number;
  read: boolean;
}
