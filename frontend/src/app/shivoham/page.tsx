'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import { API_BASE_URL } from '@/lib/constants';

interface TaskNode {
  id: string; name: string; description: string; status: string;
  dependencies: string[]; tool_name: string; result?: string; error?: string;
}
interface ExecutionEvent {
  type: string; data: Record<string, unknown>; timestamp: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  running: 'bg-blue-500/20 text-blue-400 border-blue-500/30 animate-pulse',
  completed: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/20 text-red-400 border-red-500/30',
};

export default function ShivohamPage() {
  const [goal, setGoal] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [tasks, setTasks] = useState<TaskNode[]>([]);
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [progress, setProgress] = useState({ completed: 0, total: 0, failed: 0 });
  const [planSummary, setPlanSummary] = useState('');
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight, behavior: 'smooth' });
  }, [events]);

  const handleExecute = async () => {
    if (!goal.trim() || isRunning) return;
    setIsRunning(true);
    setTasks([]);
    setEvents([]);
    setPlanSummary('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/shivoham/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal, context: '' }),
      });

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;
            try {
              const event: ExecutionEvent = JSON.parse(data);
              setEvents(prev => [...prev, event]);
              // Update state based on event type
              if (event.type === 'planning_complete') {
                setTasks((event.data.tasks as TaskNode[]) || []);
                setPlanSummary(event.data.plan_summary as string || '');
              }
              if (event.type === 'task_start') {
                setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'running' } : t));
              }
              if (event.type === 'task_complete') {
                setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'completed' } : t));
              }
              if (event.type === 'task_failed') {
                setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'failed' } : t));
              }
              if (event.type === 'engine_complete') {
                const p = event.data.progress as Record<string, number>;
                if (p) setProgress({ completed: p.completed || 0, total: p.total || 0, failed: p.failed || 0 });
              }
            } catch {}
          }
        }
      }
    } catch (err) {
      setEvents(prev => [...prev, { type: 'error', data: { error: String(err) }, timestamp: new Date().toISOString() }]);
    } finally {
      setIsRunning(false);
    }
  };

  const handleStop = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/shivoham/stop`, { method: 'POST' });
    } catch {}
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
        <h1 className="text-3xl font-heading font-bold bg-gradient-to-r from-orange-400 to-red-400 bg-clip-text text-transparent">🔱 Shivoham</h1>
        <p className="text-gray-500 mt-1">Autonomous execution engine — describe a goal and watch it come alive</p>
      </motion.div>

      {/* Goal Input */}
      <Card className="p-5">
        <label className="text-xs text-gray-500 font-medium mb-2 block">Mission Objective</label>
        <textarea value={goal} onChange={(e) => setGoal(e.target.value)}
          placeholder="Describe a complex goal... e.g., 'Research the top 5 trending AI papers this week, summarize each, and create a comparison table with key findings'"
          rows={4} className="w-full bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-sm text-white placeholder-gray-600 resize-none outline-none focus:border-orange-500/30"
        />
        <div className="flex justify-between items-center mt-3">
          <div className="flex items-center gap-3 text-xs text-gray-600">
            <span>🛡️ Sandboxed execution</span>
            <span>🔄 Self-correcting</span>
            <span>📊 Max 10 iterations</span>
          </div>
          <div className="flex gap-2">
            {isRunning && (
              <Button variant="danger" onClick={handleStop}>⏹ Stop</Button>
            )}
            <Button onClick={handleExecute} disabled={!goal.trim() || isRunning}
              className="bg-gradient-to-r from-orange-500 to-red-500 hover:shadow-[0_0_20px_rgba(249,115,22,0.3)]"
            >
              {isRunning ? '⚡ Executing...' : '🚀 Execute Mission'}
            </Button>
          </div>
        </div>
      </Card>

      {/* DAG + Execution Log */}
      {tasks.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* DAG Visualizer */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-1">Task DAG</h3>
            {planSummary && <p className="text-xs text-gray-500 mb-4">{planSummary}</p>}
            <div className="space-y-3">
              {tasks.map((task, i) => (
                <motion.div key={task.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className={`relative p-3 rounded-xl border ${STATUS_COLORS[task.status] || STATUS_COLORS.pending}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold opacity-50">{task.id}</span>
                      <span className="text-sm font-medium">{task.name}</span>
                    </div>
                    <Badge variant={task.status === 'completed' ? 'success' : task.status === 'failed' ? 'error' : task.status === 'running' ? 'processing' : 'offline'}>
                      {task.status}
                    </Badge>
                  </div>
                  {task.description && <p className="text-xs text-gray-500 mt-1">{task.description}</p>}
                  {task.dependencies.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      <span className="text-[10px] text-gray-600">deps:</span>
                      {task.dependencies.map(d => (
                        <span key={d} className="text-[10px] font-mono bg-white/[0.05] px-1.5 py-0.5 rounded">{d}</span>
                      ))}
                    </div>
                  )}
                  {/* Connection line */}
                  {i < tasks.length - 1 && (
                    <div className="absolute left-6 -bottom-3 w-px h-3 bg-white/[0.1]" />
                  )}
                </motion.div>
              ))}
            </div>
            {progress.total > 0 && (
              <div className="mt-4 pt-3 border-t border-white/[0.06]">
                <div className="flex justify-between text-xs text-gray-500 mb-2">
                  <span>Progress</span>
                  <span>{progress.completed}/{progress.total} tasks</span>
                </div>
                <div className="w-full h-2 bg-white/[0.05] rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(progress.completed / progress.total) * 100}%` }}
                    className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full"
                  />
                </div>
              </div>
            )}
          </Card>

          {/* Execution Log */}
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-3">Execution Log</h3>
            <div ref={logRef} className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin">
              <AnimatePresence>
                {events.map((event, i) => (
                  <motion.div key={i}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-xs font-mono p-2 rounded-lg bg-white/[0.02] border border-white/[0.04]"
                  >
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        event.type.includes('complete') || event.type.includes('success') ? 'bg-emerald-500' :
                        event.type.includes('fail') || event.type.includes('error') ? 'bg-red-500' :
                        event.type.includes('start') || event.type.includes('running') ? 'bg-blue-500' :
                        'bg-gray-500'
                      }`} />
                      <span className="text-gray-400">{event.type}</span>
                      <span className="text-gray-600 ml-auto">{new Date(event.timestamp).toLocaleTimeString()}</span>
                    </div>
                    {event.data && Object.keys(event.data).length > 0 && (
                      <pre className="text-gray-600 mt-1 whitespace-pre-wrap break-all">
                        {JSON.stringify(event.data, null, 2).substring(0, 200)}
                      </pre>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
