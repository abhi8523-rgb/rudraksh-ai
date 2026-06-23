"""
Neel AI — Research Module API Routes
=========================================
Deep RAG queries across uploaded papers, hypothesis generation, and literature review synthesis.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from modules.research.prompts import get_prompt
from llm.ollama_client import get_ollama_client
from llm.streaming import create_sse_stream
from memory.chroma_client import ChromaManager
from config.settings import get_settings

router = APIRouter(prefix="/api/research", tags=["Research"])


class RAGQueryRequest(BaseModel):
    question: str = Field(..., description="Research question to answer", min_length=10)
    collection: Optional[str] = Field("default", description="ChromaDB collection to query")
    num_results: int = Field(10, description="Number of context documents to retrieve", ge=1, le=50)
    depth: Optional[str] = Field("thorough", description="Analysis depth: quick, standard, thorough")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class HypothesisRequest(BaseModel):
    area: str = Field(..., description="Research area or domain")
    observations: str = Field(..., description="Current observations or known facts")
    literature: Optional[str] = Field(None, description="Summary of existing literature")
    goal: Optional[str] = Field(None, description="Research goal")
    constraints: Optional[str] = Field(None)
    num_hypotheses: Optional[str] = Field("3")
    model: Optional[str] = Field(None)
    stream: bool = Field(True)

class LitReviewRequest(BaseModel):
    topic: str = Field(..., description="Research topic for literature review")
    collection: Optional[str] = Field("default", description="ChromaDB collection to search")
    num_results: int = Field(20, description="Number of documents to include", ge=1, le=100)
    focus_areas: Optional[str] = Field(None)
    depth: Optional[str] = Field("comprehensive")
    audience: Optional[str] = Field(None)
    model: Optional[str] = Field(None)
    stream: bool = Field(True)


async def _process(action: str, params: dict, model_name: Optional[str], stream: bool):
    settings = get_settings()
    client = get_ollama_client()
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


@router.post("/query", summary="Query research documents (RAG)")
async def query_documents(req: RAGQueryRequest):
    """Perform deep RAG-powered query across uploaded research documents."""
    # Retrieve relevant context from ChromaDB
    try:
        chroma = ChromaManager()
        results = await chroma.query(
            collection_name=req.collection,
            query_text=req.question,
            n_results=req.num_results,
        )
        # Format context from retrieved documents
        context_parts = []
        if results and results.get("documents"):
            for i, (doc, meta) in enumerate(zip(
                results["documents"][0],
                results.get("metadatas", [[]])[0]
            )):
                source = meta.get("source", f"Document {i+1}") if meta else f"Document {i+1}"
                context_parts.append(f"[{source}]:\n{doc}")
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No documents found in the collection. Please upload research documents first."
    except Exception as e:
        context = f"Error retrieving documents: {str(e)}. Please ensure ChromaDB is running and documents have been uploaded."

    params = {"question": req.question, "context": context, "depth": req.depth or "thorough"}
    return await _process("query", params, req.model, req.stream)


@router.post("/hypothesis", summary="Generate research hypotheses")
async def generate_hypotheses(req: HypothesisRequest):
    """Generate testable research hypotheses based on observations and existing knowledge."""
    params = {k: v for k, v in req.model_dump(exclude={"model", "stream"}).items() if v is not None}
    return await _process("hypothesis", params, req.model, req.stream)


@router.post("/review", summary="Synthesize literature review")
async def synthesize_review(req: LitReviewRequest):
    """Create a comprehensive literature review by synthesizing uploaded research documents."""
    try:
        chroma = ChromaManager()
        results = await chroma.query(
            collection_name=req.collection,
            query_text=req.topic,
            n_results=req.num_results,
        )
        doc_parts = []
        if results and results.get("documents"):
            for i, (doc, meta) in enumerate(zip(
                results["documents"][0],
                results.get("metadatas", [[]])[0]
            )):
                source = meta.get("source", f"Paper {i+1}") if meta else f"Paper {i+1}"
                doc_parts.append(f"[{source}]:\n{doc}")
        documents = "\n\n---\n\n".join(doc_parts) if doc_parts else "No documents found. Please upload research papers first."
    except Exception as e:
        documents = f"Error retrieving documents: {str(e)}"

    params = {
        "topic": req.topic, "documents": documents,
        "focus_areas": req.focus_areas or "Not specified",
        "depth": req.depth or "comprehensive",
        "audience": req.audience or "Not specified",
    }
    return await _process("literature_review", params, req.model, req.stream)
