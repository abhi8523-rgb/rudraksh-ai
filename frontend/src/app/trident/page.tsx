'use client';

import { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '@/lib/constants';

interface TaskNode {
  id: string; name: string; description: string; status: string;
  dependencies: string[]; tool_name: string; result?: string; error?: string;
}
interface ExecutionEvent {
  type: string; data: Record<string, unknown>; timestamp: string;
}

const STATUS_COLORS: Record<string, string> = {
  pending: 'bg-slate-50 text-slate-500 border-slate-200',
  running: 'bg-blue-50 text-blue-700 border-blue-200 animate-pulse',
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  failed: 'bg-red-50 text-red-700 border-red-200',
};

export default function TridentPage() {
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
    setIsRunning(true); setTasks([]); setEvents([]); setPlanSummary('');

    try {
      const response = await fetch(`${API_BASE_URL}/api/trident/execute`, {
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
        for (const line of chunk.split('\n')) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim();
            if (data === '[DONE]') break;
            try {
              const event: ExecutionEvent = JSON.parse(data);
              setEvents(prev => [...prev, event]);
              if (event.type === 'planning_complete') {
                setTasks((event.data.tasks as TaskNode[]) || []);
                setPlanSummary(event.data.plan_summary as string || '');
              }
              if (event.type === 'task_start') setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'running' } : t));
              if (event.type === 'task_complete') setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'completed' } : t));
              if (event.type === 'task_failed') setTasks(prev => prev.map(t => t.id === event.data.task_id ? { ...t, status: 'failed' } : t));
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
    } finally { setIsRunning(false); }
  };

  const handleStop = async () => {
    try { await fetch(`${API_BASE_URL}/api/trident/stop`, { method: 'POST' }); } catch {}
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto overflow-y-auto h-full">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Trident</h1>
        <p className="text-slate-500 text-sm mt-1">Autonomous execution engine — describe a goal and watch it come alive</p>
      </div>

      {/* Goal Input */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <label className="text-xs text-slate-500 font-medium mb-2 block">Mission Objective</label>
        <textarea value={goal} onChange={(e) => setGoal(e.target.value)}
          placeholder="Describe a complex goal... e.g., 'Research the top 5 trending AI papers this week, summarize each, and create a comparison table'"
          rows={4}
          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 resize-none outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100"
        />
        <div className="flex justify-between items-center mt-3">
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span>Sandboxed execution</span>
            <span>Self-correcting</span>
            <span>Max 10 iterations</span>
          </div>
          <div className="flex gap-2">
            {isRunning && (
              <button onClick={handleStop}
                className="px-4 py-2 rounded-lg bg-red-100 text-red-700 text-sm font-medium hover:bg-red-200 transition-colors">
                Stop
              </button>
            )}
            <button onClick={handleExecute} disabled={!goal.trim() || isRunning}
              className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium disabled:opacity-40 hover:bg-blue-700 transition-colors shadow-sm">
              {isRunning ? 'Executing...' : 'Execute Mission'}
            </button>
          </div>
        </div>
      </div>

      {/* DAG + Log */}
      {tasks.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* DAG */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900 mb-1">Task DAG</h3>
            {planSummary && <p className="text-xs text-slate-500 mb-4">{planSummary}</p>}
            <div className="space-y-3">
              {tasks.map((task, i) => (
                <div key={task.id}
                  className={`relative p-3 rounded-xl border ${STATUS_COLORS[task.status] || STATUS_COLORS.pending}`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold opacity-50">{task.id}</span>
                      <span className="text-sm font-medium">{task.name}</span>
                    </div>
                    <span className="text-[10px] font-medium uppercase tracking-wider">{task.status}</span>
                  </div>
                  {task.description && <p className="text-xs text-slate-500 mt-1">{task.description}</p>}
                  {task.dependencies.length > 0 && (
                    <div className="flex gap-1 mt-2">
                      <span className="text-[10px] text-slate-400">deps:</span>
                      {task.dependencies.map(d => (
                        <span key={d} className="text-[10px] font-mono bg-slate-100 px-1.5 py-0.5 rounded">{d}</span>
                      ))}
                    </div>
                  )}
                  {i < tasks.length - 1 && <div className="absolute left-6 -bottom-3 w-px h-3 bg-slate-200" />}
                </div>
              ))}
            </div>
            {progress.total > 0 && (
              <div className="mt-4 pt-3 border-t border-slate-200">
                <div className="flex justify-between text-xs text-slate-500 mb-2">
                  <span>Progress</span>
                  <span>{progress.completed}/{progress.total} tasks</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div style={{ width: `${(progress.completed / progress.total) * 100}%` }}
                    className="h-full bg-blue-500 rounded-full transition-all duration-500" />
                </div>
              </div>
            )}
          </div>

          {/* Log */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900 mb-3">Execution Log</h3>
            <div ref={logRef} className="space-y-2 max-h-[400px] overflow-y-auto scrollbar-thin">
              {events.map((event, i) => (
                <div key={i} className="text-xs font-mono p-2 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      event.type.includes('complete') || event.type.includes('success') ? 'bg-emerald-500' :
                      event.type.includes('fail') || event.type.includes('error') ? 'bg-red-500' :
                      event.type.includes('start') || event.type.includes('running') ? 'bg-blue-500' : 'bg-slate-400'
                    }`} />
                    <span className="text-slate-700">{event.type}</span>
                    <span className="text-slate-400 ml-auto">{new Date(event.timestamp).toLocaleTimeString()}</span>
                  </div>
                  {event.data && Object.keys(event.data).length > 0 && (
                    <pre className="text-slate-500 mt-1 whitespace-pre-wrap break-all">
                      {JSON.stringify(event.data, null, 2).substring(0, 200)}
                    </pre>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
