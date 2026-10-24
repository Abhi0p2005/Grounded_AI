"""Pydantic schemas for API request/response models."""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Workspace schemas
class WorkspaceInfo(BaseModel):
    """Workspace information."""

    slug: str
    name: str
    doc_count: int = 0
    chunk_count: int = 0


class WorkspaceDetail(BaseModel):
    """Detailed workspace configuration."""

    slug: str
    name: str
    description: str
    tools: List[str]
    retrieval_settings: Dict[str, Any]
    guardrails_enabled: Dict[str, bool]


# Document schemas
class DocumentUploadResponse(BaseModel):
    """Response after document upload."""

    id: int
    filename: str
    status: str


class DocumentInfo(BaseModel):
    """Document information."""

    id: int
    filename: str
    status: str
    page_count: Optional[int] = None
    chunk_count: int = 0
    created_at: datetime
    error: Optional[str] = None


# Chat schemas
class ChatMessage(BaseModel):
    """Chat message."""

    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Chat request."""

    message: str = Field(..., min_length=1, max_length=2000)
    history: List[ChatMessage] = Field(default_factory=list, max_length=20)


class Citation(BaseModel):
    """Citation information."""

    chunk_id: int
    document: str
    page: Optional[int] = None
    score: float
    snippet: str = Field(..., max_length=200)


class ToolCall(BaseModel):
    """Tool call information."""

    name: str
    args: Dict[str, Any]
    result: Dict[str, Any]


class ChatResponse(BaseModel):
    """Chat response."""

    answer: str
    refused: bool = False
    refusal_reason: Optional[str] = None
    route: Optional[str] = None
    citations: List[Citation] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    flags: List[str] = Field(default_factory=list)
    cache_hit: bool = False
    latency_ms: int


# Chunk schema
class ChunkDetail(BaseModel):
    """Chunk detail for citation panel."""

    id: int
    text: str
    document: str
    page: Optional[int] = None
    chunk_index: int


# Query log schemas
class QueryLogEntry(BaseModel):
    """Query log entry."""

    id: int
    question_masked: str
    route: Optional[str] = None
    refused: bool
    flagged: bool
    cache_hit: bool
    latency_ms: Optional[int] = None
    top_score: Optional[float] = None
    created_at: datetime


class QueryLogDetail(BaseModel):
    """Detailed query log."""

    id: int
    question_masked: str
    route: Optional[str] = None
    answer: Optional[str] = None
    refused: bool
    refusal_reason: Optional[str] = None
    chunk_ids: List[int]
    top_score: Optional[float] = None
    tool_calls: List[Dict[str, Any]]
    flags: List[str]
    flagged: bool
    cache_hit: bool
    latency_ms: Optional[int] = None
    created_at: datetime


# Eval schemas
class EvalRunSummary(BaseModel):
    """Evaluation run summary."""

    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    metrics: Optional[Dict[str, float]] = None


class EvalRunDetail(BaseModel):
    """Detailed evaluation run results."""

    id: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    summary: Dict[str, Any]
    details: Dict[str, Any]


# Health schema
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    db: str
    redis: str
    vector_extension: bool
    llm_configured: bool


# Error schema
class ErrorDetail(BaseModel):
    """Error detail."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response."""

    error: ErrorDetail
