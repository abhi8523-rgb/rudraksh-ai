"""
Rudraksh AI — Students Module API Routes
=========================================
Study guides, concept explanation, citation assistance, and summarization.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from modules.students.prompts import get_prompt
from llm.ollama_client import OllamaClient
from llm.streaming import create_sse_stream
from config.settings import get_settings

router = APIRouter(prefix="/api/students", tags=["Students"])


class StudyGuideRequest(BaseModel):
    subject: str = Field(..., description="Academic subject")
    topic: str = Field(..., description="Specific topic to study")
    level: Optional[str] = Field(None, description="Academic level (high school, undergrad, grad)")
    exam_type: Optional[str] = Field(None, description="Type of exam preparing for")
    time_available: Optional[str] = Field(None, description="Time available for study")
    learning_style: Optional[str] = Field(None, description="Preferred learning style")
    focus_areas: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class ExplainRequest(BaseModel):
    subject: str = Field(...)
    concept: str = Field(..., description="Concept to explain")
    level: Optional[str] = Field(None)
    prior_knowledge: Optional[str] = Field(None, description="What you already know")
    purpose: Optional[str] = Field(None, description="Why you need to learn this")
    style: Optional[str] = Field(None, description="Preferred explanation style")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class CitationRequest(BaseModel):
    format: str = Field(..., description="Citation format (APA, MLA, Chicago, IEEE, Harvard)")
    source_info: str = Field(..., description="Source information to format")
    source_type: Optional[str] = Field(None, description="Type of source (book, journal, website)")
    task: Optional[str] = Field(None, description="Specific citation task")
    requirements: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class SummarizeRequest(BaseModel):
    content: str = Field(..., description="Content to summarize", min_length=50)
    style: Optional[str] = Field(None, description="Summary style (executive, key points, structured)")
    target_length: Optional[str] = Field(None, description="Target summary length")
    purpose: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)


async def _process(action: str, params: dict, model_name: Optional[str], stream: bool):
    settings = get_settings()
    client = OllamaClient()
    try:
        prompts = get_prompt(action, **params)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    use_model = model_name or settings.default_model
    messages = [{"role": "system", "content": prompts["system"]}, {"role": "user", "content": prompts["user"]}]
    if stream:
        async def gen():
            async for chunk in client.chat_stream(model=use_model, messages=messages):
                yield chunk
        return create_sse_stream(gen())
    else:
        resp = await client.chat(model=use_model, messages=messages)
        return {"action": action, "content": resp.get("message", {}).get("content", ""), "model_used": use_model}


@router.post("/guide", summary="Generate study guide")
async def create_study_guide(req: StudyGuideRequest):
    """Create a personalized, comprehensive study guide for any topic."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("study_guide", params, req.model, req.stream)

@router.post("/explain", summary="Explain a concept")
async def explain_concept(req: ExplainRequest):
    """Get a clear, multi-level explanation of any complex concept."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("explain", params, req.model, req.stream)

@router.post("/cite", summary="Format citations")
async def format_citation(req: CitationRequest):
    """Format citations in APA, MLA, Chicago, IEEE, or Harvard style."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("cite", params, req.model, req.stream)

@router.post("/summarize", summary="Summarize content")
async def summarize_content(req: SummarizeRequest):
    """Create concise, accurate summaries of academic content."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("summarize", params, req.model, req.stream)
