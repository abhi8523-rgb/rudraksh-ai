"""
Rudraksh AI — Marketing Module API Routes
==========================================
Campaign strategy, SEO analysis, A/B testing, and customer personas.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from modules.marketing.prompts import get_prompt
from llm.ollama_client import get_ollama_client
from llm.streaming import create_sse_stream
from config.settings import get_settings

router = APIRouter(prefix="/api/marketing", tags=["Marketing"])


class CampaignRequest(BaseModel):
    product: str = Field(..., description="Product or service name")
    industry: str = Field(..., description="Industry vertical")
    goal: str = Field(..., description="Primary campaign goal")
    target_market: Optional[str] = Field(None)
    budget: Optional[str] = Field(None)
    duration: Optional[str] = Field(None)
    constraints: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class SEORequest(BaseModel):
    website: str = Field(..., description="Website URL or business name")
    industry: str = Field(...)
    current_keywords: Optional[str] = Field(None)
    competitors: Optional[str] = Field(None)
    audience: Optional[str] = Field(None)
    goals: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class ABTestRequest(BaseModel):
    element: str = Field(..., description="Element to test (e.g., landing page headline)")
    goal: str = Field(..., description="Test goal")
    current_performance: Optional[str] = Field(None)
    platform: Optional[str] = Field(None)
    audience_size: Optional[str] = Field(None)
    constraints: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class PersonaRequest(BaseModel):
    product: str = Field(...)
    industry: str = Field(...)
    segment: Optional[str] = Field(None)
    num_personas: Optional[str] = Field("2")
    customer_data: Optional[str] = Field(None)
    goals: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)


async def _process(action: str, params: dict, model: Optional[str], stream: bool):
    settings = get_settings()
    client = get_ollama_client()
    try:
        prompts = get_prompt(action, **params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    use_model = model or settings.default_model
    messages = [{"role": "system", "content": prompts["system"]}, {"role": "user", "content": prompts["user"]}]
    if stream:
        async def gen():
            async for chunk in client.chat_stream(model=use_model, messages=messages):
                yield chunk
        return create_sse_stream(gen())
    else:
        resp = await client.chat(model=use_model, messages=messages)
        return {"action": action, "content": resp.get("message", {}).get("content", ""), "model_used": use_model}


@router.post("/campaign", summary="Create campaign strategy")
async def create_campaign(req: CampaignRequest):
    """Generate a comprehensive marketing campaign strategy."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("campaign", params, req.model, req.stream)

@router.post("/seo", summary="SEO analysis")
async def analyze_seo(req: SEORequest):
    """Perform SEO analysis with keyword research and optimization recommendations."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("seo", params, req.model, req.stream)

@router.post("/ab-test", summary="Generate A/B tests")
async def generate_ab_tests(req: ABTestRequest):
    """Design rigorous A/B test plans for marketing elements."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("ab_test", params, req.model, req.stream)

@router.post("/persona", summary="Develop customer personas")
async def create_personas(req: PersonaRequest):
    """Create detailed customer personas for targeted marketing."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("persona", params, req.model, req.stream)
