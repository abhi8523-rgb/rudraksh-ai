"""
Rudraksh AI — Shivoham Core Execution Engine
=============================================
The autonomous execution loop: plan → execute → verify → correct → repeat.
Orchestrates DAG planning, tool execution, and self-correction.
"""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Optional

from shivoham.dag import DAGPlanner, TaskNode, TaskStatus
from shivoham.tools import ShivohamTools, ToolResult
from shivoham.verifier import Verifier
from shivoham.sandbox import Sandbox
from config.settings import get_settings


class ExecutionEvent:
    """An event emitted during execution for real-time streaming."""
    def __init__(self, event_type: str, data: dict):
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()

    def to_sse(self) -> str:
        payload = json.dumps({
            "type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp,
        })
        return f"data: {payload}\n\n"


class ShivohamEngine:
    """The core autonomous execution engine.
    
    Workflow:
    1. Receive high-level goal from user
    2. Use LLM to decompose into a DAG of subtasks
    3. Execute tasks in topological order
    4. Verify each task's result
    5. Retry or re-plan on failure
    6. Stream events in real-time
    """

    def __init__(self):
        self._settings = get_settings()
        self._sandbox = Sandbox()
        self._planner = DAGPlanner()
        self._tools = ShivohamTools(self._sandbox)
        self._verifier = Verifier()
        self._max_iterations = self._settings.shivoham_max_iterations
        self._execution_log: list[dict] = []
        self._is_running = False
        self._should_stop = False

    async def execute(self, goal: str, context: str = "") -> AsyncGenerator[ExecutionEvent, None]:
        """Execute a high-level goal autonomously.
        
        Yields ExecutionEvent objects for real-time streaming.
        
        Args:
            goal: High-level goal description
            context: Additional context or constraints
        """
        self._is_running = True
        self._should_stop = False
        self._execution_log = []
        iteration = 0

        yield ExecutionEvent("engine_start", {
            "goal": goal,
            "max_iterations": self._max_iterations,
            "sandbox": self._sandbox.get_info(),
        })

        try:
            # Phase 1: Plan
            yield ExecutionEvent("planning_start", {"goal": goal})
            
            try:
                tasks = await self._planner.plan(goal, context)
                yield ExecutionEvent("planning_complete", {
                    "plan_summary": self._planner.plan_summary,
                    "task_count": len(tasks),
                    "tasks": [t.to_dict() for t in tasks],
                })
            except Exception as e:
                yield ExecutionEvent("planning_failed", {"error": str(e)})
                yield ExecutionEvent("engine_complete", {
                    "success": False,
                    "error": f"Planning failed: {e}",
                })
                return

            # Phase 2: Execute tasks
            task_outputs: dict[str, str] = {}  # task_id -> output

            while not self._planner.is_complete() and iteration < self._max_iterations:
                if self._should_stop:
                    yield ExecutionEvent("engine_stopped", {"reason": "User requested stop"})
                    break

                iteration += 1
                ready_tasks = self._planner.get_ready_tasks()

                if not ready_tasks:
                    # Check if we're stuck (all remaining tasks have failed deps)
                    pending = [t for t in self._planner.tasks.values() if t.status == TaskStatus.PENDING]
                    if pending:
                        yield ExecutionEvent("execution_stuck", {
                            "pending_tasks": [t.name for t in pending],
                            "reason": "No tasks ready — dependencies may have failed",
                        })
                    break

                for task in ready_tasks:
                    if self._should_stop:
                        break

                    # Execute the task
                    yield ExecutionEvent("task_start", {
                        "task_id": task.id,
                        "task_name": task.name,
                        "tool": task.tool_name,
                        "iteration": iteration,
                    })

                    self._planner.mark_running(task.id)

                    # Execute tool
                    result = await self._tools.execute(
                        tool_name=task.tool_name or "llm_query",
                        tool_args=task.tool_args,
                        task_context=task_outputs,
                    )

                    yield ExecutionEvent("task_executed", {
                        "task_id": task.id,
                        "success": result.success,
                        "output_preview": result.output[:500],
                        "duration_ms": result.duration_ms,
                    })

                    # Phase 3: Verify
                    verification = await self._verifier.verify(
                        task_name=task.name,
                        task_description=task.description,
                        task_result=result.output,
                        tool_name=result.tool_name,
                        was_success=result.success,
                    )

                    yield ExecutionEvent("task_verified", {
                        "task_id": task.id,
                        "verdict": verification["verdict"],
                        "quality_score": verification["quality_score"],
                        "issues": verification.get("issues", []),
                    })

                    if verification["verdict"] in ("success", "partial"):
                        self._planner.mark_completed(task.id, result.output)
                        task_outputs[task.id] = result.output

                        yield ExecutionEvent("task_complete", {
                            "task_id": task.id,
                            "task_name": task.name,
                            "verdict": verification["verdict"],
                        })
                    else:
                        # Check if we should retry
                        should_retry = await self._verifier.should_retry(
                            verification, task.retries, task.max_retries
                        )

                        if should_retry:
                            task.retries += 1
                            task.status = TaskStatus.PENDING  # Reset for retry

                            yield ExecutionEvent("task_retry", {
                                "task_id": task.id,
                                "task_name": task.name,
                                "retry_num": task.retries,
                                "suggestion": verification.get("retry_suggestion"),
                            })

                            # Modify tool args with retry context
                            retry_ctx = await self._verifier.generate_retry_context(
                                task.name, result.output, verification
                            )
                            if "prompt" in task.tool_args:
                                task.tool_args["prompt"] = f"{retry_ctx}\n\n{task.tool_args['prompt']}"
                        else:
                            self._planner.mark_failed(task.id, result.output)

                            yield ExecutionEvent("task_failed", {
                                "task_id": task.id,
                                "task_name": task.name,
                                "error": result.output[:500],
                                "needs_replan": verification.get("needs_replan", False),
                            })

                            # If replan is needed, try to create a new plan
                            if verification.get("needs_replan", False):
                                yield ExecutionEvent("replanning_start", {
                                    "reason": f"Task '{task.name}' requires different approach",
                                })
                                try:
                                    failed_tasks = [
                                        t for t in self._planner.tasks.values()
                                        if t.status == TaskStatus.FAILED
                                    ]
                                    tasks = await self._planner.replan(goal, failed_tasks, context)
                                    yield ExecutionEvent("replanning_complete", {
                                        "new_task_count": len(tasks),
                                        "tasks": [t.to_dict() for t in tasks],
                                    })
                                except Exception as e:
                                    yield ExecutionEvent("replanning_failed", {"error": str(e)})

                    # Log execution
                    self._execution_log.append({
                        "iteration": iteration,
                        "task_id": task.id,
                        "task_name": task.name,
                        "tool": task.tool_name,
                        "success": result.success,
                        "verification": verification["verdict"],
                        "timestamp": datetime.utcnow().isoformat(),
                    })

            # Phase 4: Summary
            progress = self._planner.get_progress()
            all_succeeded = progress["failed"] == 0 and progress["completed"] == progress["total"]

            yield ExecutionEvent("engine_complete", {
                "success": all_succeeded,
                "progress": progress,
                "iterations_used": iteration,
                "max_iterations": self._max_iterations,
                "execution_log": self._execution_log,
                "plan": self._planner.to_dict(),
            })

        except Exception as e:
            yield ExecutionEvent("engine_error", {
                "error": str(e),
                "type": type(e).__name__,
            })
        finally:
            self._is_running = False

    def stop(self):
        """Request the engine to stop execution."""
        self._should_stop = True

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_status(self) -> dict:
        """Get current engine status."""
        return {
            "is_running": self._is_running,
            "plan": self._planner.to_dict() if self._planner.tasks else None,
            "execution_log": self._execution_log[-10:],  # Last 10 entries
        }
