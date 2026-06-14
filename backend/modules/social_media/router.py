"""
Rudraksh AI — Social Media Module API Routes
=============================================
Endpoints for content calendar, trend analysis, post drafting, and engagement simulation.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from modules.social_media.prompts import get_prompt
from llm.ollama_client import OllamaClient
from llm.streaming import create_sse_stream
from config.settings import get_settings

router = APIRouter(prefix="/api/social", tags=["Social Media"])


class CalendarRequest(BaseModel):
    duration: str = Field(..., description="Calendar duration", examples=["1 week", "1 month"])
    platforms: str = Field(..., description="Target platforms", examples=["Instagram, Twitter, LinkedIn"])
    niche: str = Field(..., description="Industry or niche")
    brand_voice: Optional[str] = Field(None, description="Brand voice description")
    goals: Optional[str] = Field(None, description="Campaign goals")
    notes: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class TrendRequest(BaseModel):
    platforms: str = Field(..., description="Platforms to analyze")
    niche: str = Field(..., description="Industry or niche")
    audience: Optional[str] = Field(None, description="Target audience demographics")
    region: Optional[str] = Field(None, description="Geographic region")
    time_period: Optional[str] = Field(None, description="Time period for analysis")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class DraftRequest(BaseModel):
    platform: str = Field(..., description="Target platform")
    topic: str = Field(..., description="Post topic or theme")
    num_variations: Optional[str] = Field("3", description="Number of variations to generate")
    brand_voice: Optional[str] = Field(None)
    goal: Optional[str] = Field(None, description="Post goal (engagement, awareness, conversion)")
    key_message: Optional[str] = Field(None)
    include_elements: Optional[str] = Field(None, description="Elements to include (emojis, hashtags, CTA)")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class EngagementRequest(BaseModel):
    platform: str = Field(..., description="Target platform")
    content: str = Field(..., description="Content to simulate")
    audience_size: Optional[str] = Field(None)
    niche: Optional[str] = Field(None)
    posting_time: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)


async def _process_request(action: str, params: dict, model: Optional[str], stream: bool):
    settings = get_settings()
    client = OllamaClient()
    try:
        prompts = get_prompt(action, **params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    use_model = model or settings.default_model
    messages = [
        {"role": "system", "content": prompts["system"]},
        {"role": "user", "content": prompts["user"]},
    ]
    if stream:
        async def generate():
            async for chunk in client.chat_stream(model=use_model, messages=messages):
                yield chunk
        return create_sse_stream(generate())
    else:
        response = await client.chat(model=use_model, messages=messages)
        return {"action": action, "content": response.get("message", {}).get("content", ""), "model_used": use_model}


@router.post("/calendar", summary="Generate content calendar")
async def create_calendar(request: CalendarRequest):
    """Generate a strategic content calendar for specified platforms and duration."""
    params = {k: v for k, v in request.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process_request("calendar", params, request.model, request.stream)


@router.post("/trends", summary="Analyze social media trends")
async def analyze_trends(request: TrendRequest):
    """Identify and analyze current and emerging trends for a niche."""
    params = {k: v for k, v in request.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process_request("trends", params, request.model, request.stream)


@router.post("/draft", summary="Draft social media posts")
async def draft_posts(request: DraftRequest):
    """Create platform-optimized post drafts with multiple variations."""
    params = {k: v for k, v in request.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process_request("draft", params, request.model, request.stream)


@router.post("/engagement", summary="Simulate content engagement")
async def simulate_engagement(request: EngagementRequest):
    """Predict engagement metrics and suggest optimizations for content."""
    params = {k: v for k, v in request.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process_request("engagement", params, request.model, request.stream)
