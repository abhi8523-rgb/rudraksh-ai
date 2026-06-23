"""
Neel AI — Trident Tool Definitions
========================================
Sandboxed tools accessible by the autonomous execution engine:
terminal, file system, web, LLM, and memory.
"""

import asyncio
import subprocess
from typing import Optional
from datetime import datetime

from trident.sandbox import Sandbox, SandboxViolation
from llm.ollama_client import OllamaClient
from memory.chroma_client import ChromaManager
from config.settings import get_settings


class ToolResult:
    """Result of a tool execution."""
    def __init__(self, success: bool, output: str, tool_name: str, duration_ms: int = 0):
        self.success = success
        self.output = output
        self.tool_name = tool_name
        self.duration_ms = duration_ms
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output[:5000],  # Cap output in serialization
            "tool_name": self.tool_name,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }


class TridentTools:
    """Collection of sandboxed tools for the Trident execution engine."""

    def __init__(self, sandbox: Optional[Sandbox] = None):
        self._sandbox = sandbox or Sandbox()
        self._client = OllamaClient()
        self._settings = get_settings()

    async def execute(self, tool_name: str, tool_args: dict, task_context: dict = None) -> ToolResult:
        """Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            task_context: Context from completed dependency tasks
            
        Returns:
            ToolResult with success status and output
        """
        # Resolve references to previous task outputs
        if task_context:
            tool_args = self._resolve_references(tool_args, task_context)

        tool_map = {
            "llm_query": self._tool_llm_query,
            "terminal": self._tool_terminal,
            "file_read": self._tool_file_read,
            "file_write": self._tool_file_write,
            "memory_search": self._tool_memory_search,
            "memory_store": self._tool_memory_store,
        }

        handler = tool_map.get(tool_name)
        if not handler:
            return ToolResult(
                success=False,
                output=f"Unknown tool: '{tool_name}'. Available: {list(tool_map.keys())}",
                tool_name=tool_name,
            )

        start = datetime.utcnow()
        try:
            result = await handler(**tool_args)
            duration = int((datetime.utcnow() - start).total_seconds() * 1000)
            return ToolResult(success=True, output=result, tool_name=tool_name, duration_ms=duration)
        except SandboxViolation as e:
            return ToolResult(success=False, output=f"SANDBOX VIOLATION: {e}", tool_name=tool_name)
        except Exception as e:
            duration = int((datetime.utcnow() - start).total_seconds() * 1000)
            return ToolResult(
                success=False,
                output=f"Tool execution error: {type(e).__name__}: {e}",
                tool_name=tool_name,
                duration_ms=duration,
            )

    def _resolve_references(self, args: dict, context: dict) -> dict:
        """Replace content_source references with actual task outputs."""
        resolved = {}
        for key, value in args.items():
            if key == "content_source" and isinstance(value, str):
                # Replace with the output from the referenced task
                resolved["content"] = context.get(value, f"[Output from {value} not available]")
            elif isinstance(value, str) and value.startswith("$"):
                # $t1 style reference
                ref_id = value[1:]
                resolved[key] = context.get(ref_id, value)
            else:
                resolved[key] = value
        return resolved

    async def _tool_llm_query(self, prompt: str = "", system: str = "", **kwargs) -> str:
        """Query the local LLM with a prompt."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt or str(kwargs)})

        response = await self._client.chat(
            model=self._settings.default_model,
            messages=messages,
        )
        return response.get("message", {}).get("content", "No response from model")

    async def _tool_terminal(self, command: str = "", **kwargs) -> str:
        """Execute a shell command in the sandbox."""
        validated_cmd = self._sandbox.validate_command(command)
        
        timeout = min(int(kwargs.get("timeout", 30)), self._settings.Trident_task_timeout)

        try:
            process = await asyncio.create_subprocess_shell(
                validated_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._sandbox.root),
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            output = stdout.decode("utf-8", errors="replace")
            if stderr:
                output += f"\nSTDERR:\n{stderr.decode('utf-8', errors='replace')}"
            
            output = self._sandbox.truncate_output(output)
            
            if process.returncode != 0:
                return f"Command exited with code {process.returncode}\n{output}"
            return output

        except asyncio.TimeoutError:
            process.kill()
            return f"Command timed out after {timeout} seconds"

    async def _tool_file_read(self, path: str = "", **kwargs) -> str:
        """Read a file from the sandbox."""
        validated_path = self._sandbox.validate_file_read(path)
        content = validated_path.read_text(encoding="utf-8", errors="replace")
        return self._sandbox.truncate_output(content)

    async def _tool_file_write(self, path: str = "", content: str = "", **kwargs) -> str:
        """Write content to a file in the sandbox."""
        validated_path = self._sandbox.validate_file_write(path, content)
        validated_path.parent.mkdir(parents=True, exist_ok=True)
        validated_path.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} characters to {validated_path.name}"

    async def _tool_memory_search(self, query: str = "", collection: str = "default", n_results: int = 5, **kwargs) -> str:
        """Search the vector database."""
        try:
            chroma = ChromaManager()
            results = await chroma.query(
                collection_name=collection,
                query_text=query,
                n_results=n_results,
            )
            if results and results.get("documents"):
                docs = results["documents"][0]
                return "\n\n---\n\n".join(
                    f"[Result {i+1}]: {doc}" for i, doc in enumerate(docs)
                )
            return "No relevant documents found."
        except Exception as e:
            return f"Memory search error: {e}"

    async def _tool_memory_store(self, content: str = "", metadata: dict = None, collection: str = "default", **kwargs) -> str:
        """Store information in the vector database."""
        try:
            chroma = ChromaManager()
            import uuid
            doc_id = str(uuid.uuid4())[:8]
            await chroma.add_documents(
                collection_name=collection,
                documents=[content],
                metadatas=[metadata or {"source": "Trident"}],
                ids=[doc_id],
            )
            return f"Stored document with ID: {doc_id}"
        except Exception as e:
            return f"Memory store error: {e}"

    def get_available_tools(self) -> list[dict]:
        """Return descriptions of all available tools."""
        return [
            {"name": "llm_query", "description": "Query the AI model", "args": ["prompt", "system"]},
            {"name": "terminal", "description": "Execute a shell command (sandboxed)", "args": ["command", "timeout"]},
            {"name": "file_read", "description": "Read a file from sandbox", "args": ["path"]},
            {"name": "file_write", "description": "Write to a file in sandbox", "args": ["path", "content"]},
            {"name": "memory_search", "description": "Search vector database", "args": ["query", "collection", "n_results"]},
            {"name": "memory_store", "description": "Store in vector database", "args": ["content", "metadata", "collection"]},
        ]
