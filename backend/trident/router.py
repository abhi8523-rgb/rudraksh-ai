"""
Neel AI — Trident API Routes
==================================
Endpoints for the autonomous execution engine.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional

from trident.engine import TridentEngine

router = APIRouter(prefix="/api/trident", tags=["Trident"])

# Global engine instance (one active execution at a time)
_engine: Optional[TridentEngine] = None


class GoalRequest(BaseModel):
    goal: str = Field(..., description="High-level goal to execute", min_length=10)
    context: Optional[str] = Field(None, description="Additional context or constraints")

class GoalResponse(BaseModel):
    status: str
    message: str


@router.post("/execute", summary="Execute an autonomous goal")
async def execute_goal(request: GoalRequest):
    """Submit a high-level goal for autonomous execution by the Trident engine.
    
    Returns a streaming SSE response with real-time execution events.
    The engine will:
    1. Decompose the goal into a DAG of subtasks
    2. Execute each task with appropriate tools
    3. Verify results and self-correct on failure
    4. Stream progress events throughout
    """
    global _engine
    
    if _engine and _engine.is_running:
        raise HTTPException(
            status_code=409,
            detail="Another execution is already in progress. Stop it first or wait for completion."
        )

    _engine = TridentEngine()

    async def event_stream():
        async for event in _engine.execute(
            goal=request.goal,
            context=request.context or ""
        ):
            yield event.to_sse()
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/stop", summary="Stop current execution")
async def stop_execution():
    """Request the Trident engine to stop the current execution gracefully."""
    global _engine
    if not _engine or not _engine.is_running:
        raise HTTPException(status_code=404, detail="No active execution to stop")
    
    _engine.stop()
    return {"status": "stopping", "message": "Stop signal sent. Engine will halt after current task."}


@router.get("/status", summary="Get engine status")
async def get_status():
    """Get the current status of the Trident engine."""
    global _engine
    if not _engine:
        return {"is_running": False, "plan": None, "execution_log": []}
    return _engine.get_status()


@router.get("/tools", summary="List available tools")
async def list_tools():
    """List all tools available to the Trident engine."""
    from trident.tools import TridentTools
    tools = TridentTools()
    return {"tools": tools.get_available_tools()}
