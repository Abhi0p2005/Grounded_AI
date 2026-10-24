"""SQLAlchemy ORM models."""
from datetime import datetime
from typing import List

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.types import DateTime

from app.db import Base


class Workspace(Base):
    """Workspace model - isolated knowledge base."""

    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    config_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    chunks = relationship("Chunk", back_populates="workspace", cascade="all, delete-orphan")
    query_logs = relationship("QueryLog", back_populates="workspace", cascade="all, delete-orphan")
    eval_runs = relationship("EvalRun", back_populates="workspace", cascade="all, delete-orphan")


class Document(Base):
    """Document model - uploaded files."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    sha256 = Column(String, nullable=False)
    page_count = Column(Integer)
    status = Column(String, nullable=False, default="pending")
    error = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Chunk model - document fragments with embeddings."""

    __tablename__ = "chunks"

    id = Column(BigInteger, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    tsv = Column(
        TSVECTOR,
        server_default=sql_text("to_tsvector('english', text)"),
    )

    workspace = relationship("Workspace", back_populates="chunks")
    document = relationship("Document", back_populates="chunks")


class QueryLog(Base):
    """Query log model - chat interaction logs."""

    __tablename__ = "query_logs"

    id = Column(BigInteger, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    question_masked = Column(Text, nullable=False)
    route = Column(String)
    answer = Column(Text)
    refused = Column(Boolean, nullable=False, default=False)
    refusal_reason = Column(String)
    chunk_ids = Column(ARRAY(BigInteger), default=[])
    top_score = Column(Float)
    tool_calls = Column(JSONB, default=[])
    flags = Column(ARRAY(String), default=[])
    flagged = Column(Boolean, nullable=False, default=False)
    cache_hit = Column(Boolean, nullable=False, default=False)
    latency_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="query_logs")


class EvalRun(Base):
    """Evaluation run model - quality metrics."""

    __tablename__ = "eval_runs"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    summary = Column(JSONB)
    details = Column(JSONB)

    workspace = relationship("Workspace", back_populates="eval_runs")
