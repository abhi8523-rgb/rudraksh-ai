"""
Neel AI — Trident DAG Task Planner
========================================
Breaks high-level goals into a Directed Acyclic Graph (DAG) of subtasks,
determines execution order via topological sort, and supports dynamic re-planning.
"""

from __future__ import annotations
import uuid
import json
import graphlib
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from llm.ollama_client import OllamaClient
from config.settings import get_settings


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class TaskNode:
    """Represents a single task in the DAG."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: dict = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 2
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "retries": self.retries,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


DAG_PLANNING_SYSTEM = """You are the Trident task planner — an expert at decomposing complex goals 
into structured execution plans.

Given a high-level goal, you must:
1. Break it down into atomic, executable subtasks
2. Identify dependencies between tasks (which tasks must complete before others)
3. Assign appropriate tools to each task

AVAILABLE TOOLS:
- "llm_query": Ask the AI model a question or generate content
- "terminal": Execute a shell command (sandboxed)
- "file_read": Read a file from the filesystem (sandboxed)
- "file_write": Write content to a file (sandboxed)
- "memory_search": Search the vector database for relevant documents
- "memory_store": Store information in the vector database
- "web_search": Search the web for information

RESPONSE FORMAT (strict JSON):
{
    "plan_summary": "Brief description of the overall execution plan",
    "tasks": [
        {
            "id": "t1",
            "name": "Short task name",
            "description": "What this task does in detail",
            "dependencies": [],
            "tool_name": "llm_query",
            "tool_args": {"prompt": "the query to send"}
        },
        {
            "id": "t2", 
            "name": "Another task",
            "description": "Details...",
            "dependencies": ["t1"],
            "tool_name": "file_write",
            "tool_args": {"path": "output.md", "content_source": "t1"}
        }
    ]
}

RULES:
- Each task must have a unique ID (t1, t2, t3, etc.)
- Dependencies reference task IDs that must complete first
- No circular dependencies allowed
- Keep tasks atomic — one clear action per task
- Use "content_source" in tool_args to reference output from a dependency
- Maximum 15 tasks per plan (break very complex goals into phases)
- Always respond with ONLY valid JSON, no markdown fences"""


class DAGPlanner:
    """Plans and manages task DAGs for the Trident engine."""

    def __init__(self):
        self.tasks: dict[str, TaskNode] = {}
        self.plan_summary: str = ""
        self._client = OllamaClient()

    async def plan(self, goal: str, context: str = "") -> list[TaskNode]:
        """Use LLM to decompose a goal into a DAG of tasks.
        
        Args:
            goal: The high-level goal to decompose
            context: Additional context or constraints
            
        Returns:
            List of TaskNode objects in topological order
        """
        settings = get_settings()
        
        user_prompt = f"Goal: {goal}"
        if context:
            user_prompt += f"\n\nAdditional Context: {context}"

        messages = [
            {"role": "system", "content": DAG_PLANNING_SYSTEM},
            {"role": "user", "content": user_prompt},
        ]

        response = await self._client.chat(
            model=settings.default_model,
            messages=messages,
        )

        content = response.get("message", {}).get("content", "")
        
        # Parse the JSON response
        try:
            # Clean up potential markdown fencing
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1]
                content = content.rsplit("```", 1)[0]
            
            plan_data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse task plan from LLM: {e}\nRaw output: {content[:500]}")

        self.plan_summary = plan_data.get("plan_summary", "No summary provided")
        
        # Create TaskNode objects
        self.tasks.clear()
        for task_data in plan_data.get("tasks", []):
            node = TaskNode(
                id=task_data["id"],
                name=task_data.get("name", "Unnamed Task"),
                description=task_data.get("description", ""),
                dependencies=task_data.get("dependencies", []),
                tool_name=task_data.get("tool_name"),
                tool_args=task_data.get("tool_args", {}),
            )
            self.tasks[node.id] = node

        # Validate the DAG (check for cycles)
        self._validate_dag()

        return self.get_execution_order()

    def _validate_dag(self) -> None:
        """Validate the DAG has no cycles and all dependencies exist."""
        # Check that all dependencies reference existing tasks
        all_ids = set(self.tasks.keys())
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in all_ids:
                    raise ValueError(
                        f"Task '{task.id}' depends on '{dep_id}' which doesn't exist"
                    )
        
        # Check for cycles using graphlib
        dep_graph = {
            task_id: set(task.dependencies)
            for task_id, task in self.tasks.items()
        }
        try:
            sorter = graphlib.TopologicalSorter(dep_graph)
            list(sorter.static_order())  # Will raise CycleError if cycles exist
        except graphlib.CycleError as e:
            raise ValueError(f"Circular dependency detected in task plan: {e}")

    def get_execution_order(self) -> list[TaskNode]:
        """Return tasks in topological execution order."""
        dep_graph = {
            task_id: set(task.dependencies)
            for task_id, task in self.tasks.items()
        }
        sorter = graphlib.TopologicalSorter(dep_graph)
        ordered_ids = list(sorter.static_order())
        return [self.tasks[tid] for tid in ordered_ids]

    def get_ready_tasks(self) -> list[TaskNode]:
        """Return tasks whose dependencies are all completed."""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            deps_met = all(
                self.tasks[dep_id].status == TaskStatus.COMPLETED
                for dep_id in task.dependencies
                if dep_id in self.tasks
            )
            if deps_met:
                ready.append(task)
        return ready

    def mark_completed(self, task_id: str, result: str) -> None:
        """Mark a task as completed with its result."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow().isoformat()

    def mark_failed(self, task_id: str, error: str) -> None:
        """Mark a task as failed with error details."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.FAILED
            task.error = error
            task.completed_at = datetime.utcnow().isoformat()

    def mark_running(self, task_id: str) -> None:
        """Mark a task as currently running."""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow().isoformat()

    def is_complete(self) -> bool:
        """Check if all tasks are completed or failed."""
        return all(
            t.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED)
            for t in self.tasks.values()
        )

    def get_progress(self) -> dict:
        """Get progress statistics."""
        total = len(self.tasks)
        statuses = {}
        for task in self.tasks.values():
            statuses[task.status.value] = statuses.get(task.status.value, 0) + 1
        return {
            "total": total,
            "completed": statuses.get("completed", 0),
            "failed": statuses.get("failed", 0),
            "running": statuses.get("running", 0),
            "pending": statuses.get("pending", 0),
            "progress_pct": round(
                (statuses.get("completed", 0) + statuses.get("failed", 0)) / total * 100
                if total > 0 else 0, 1
            ),
        }

    def to_dict(self) -> dict:
        """Serialize the entire DAG to a dictionary."""
        return {
            "plan_summary": self.plan_summary,
            "tasks": [t.to_dict() for t in self.get_execution_order()],
            "progress": self.get_progress(),
        }

    async def replan(self, goal: str, failed_tasks: list[TaskNode], context: str = "") -> list[TaskNode]:
        """Re-plan after failures, incorporating failure information."""
        failure_info = "\n".join(
            f"- Task '{t.name}' (ID: {t.id}) failed: {t.error}" for t in failed_tasks
        )
        augmented_context = f"""{context}

PREVIOUS FAILURES (avoid the same approaches):
{failure_info}

Please create an alternative plan that works around these failures."""

        return await self.plan(goal, augmented_context)
