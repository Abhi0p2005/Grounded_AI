"""Ingestion pipeline: parse -> chunk -> embed -> store."""
import hashlib
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy.exc import IntegrityError

from app.core.embeddings import get_embedding_model
from app.core.workspace_config import get_docs_dir, load_workspace_config
from app.db import db_session
from app.ingestion.chunker import chunk_pages
from app.ingestion.parsers import parse_pdf
from app.models import Chunk, Document, Workspace

logger = logging.getLogger(__name__)


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def ingest_file(workspace_slug: str, file_path: Path) -> dict:
    """
    Ingest a single PDF file into the workspace.
    
    Args:
        workspace_slug: Workspace identifier
        file_path: Path to PDF file
        
    Returns:
        Dict with status info: {id, filename, status, error}
        
    Process:
        1. Compute SHA256 hash for idempotency
        2. Check if already ingested (workspace + hash)
        3. Parse PDF -> pages
        4. Chunk pages -> chunks
        5. Embed chunks in batches
        6. Store in database
        7. Mark document as ready
    """
    filename = file_path.name
    logger.info(f"Starting ingestion: {workspace_slug}/{filename}")
    
    try:
        # Compute hash for idempotency
        file_hash = compute_file_hash(file_path)
        
        with db_session() as db:
            # Get workspace
            workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
            if not workspace:
                raise ValueError(f"Workspace not found: {workspace_slug}")
            
            # Check if already ingested
            existing = (
                db.query(Document)
                .filter(
                    Document.workspace_id == workspace.id,
                    Document.sha256 == file_hash,
                )
                .first()
            )
            
            if existing and existing.status == "ready":
                logger.info(f"Document already ingested: {filename} (id={existing.id})")
                return {
                    "id": existing.id,
                    "filename": filename,
                    "status": "ready",
                    "error": None,
                }
            
            # Create or update document record
            if existing:
                doc = existing
                doc.status = "pending"
                doc.error = None
            else:
                doc = Document(
                    workspace_id=workspace.id,
                    filename=filename,
                    sha256=file_hash,
                    status="pending",
                )
                db.add(doc)
                db.flush()
            
            doc_id = doc.id
            
            try:
                # Parse PDF
                logger.info(f"Parsing PDF: {filename}")
                pages = parse_pdf(file_path)
                doc.page_count = len(pages)
                
                # Chunk pages
                logger.info(f"Chunking {len(pages)} pages")
                chunks = chunk_pages(pages, target_tokens=500, overlap_tokens=80)
                
                # Embed chunks in batches
                logger.info(f"Embedding {len(chunks)} chunks")
                embedding_model = get_embedding_model()
                texts = [chunk.text for chunk in chunks]
                embeddings = embedding_model.encode_documents(texts, batch_size=32)
                
                # Store chunks
                logger.info(f"Storing {len(chunks)} chunks to database")
                for i, (chunk_info, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk = Chunk(
                        workspace_id=workspace.id,
                        document_id=doc_id,
                        chunk_index=i,
                        page_number=chunk_info.page_number,
                        text=chunk_info.text,
                        token_count=chunk_info.token_count,
                        embedding=embedding,
                    )
                    db.add(chunk)
                
                # Mark as ready
                doc.status = "ready"
                db.commit()
                
                logger.info(f"Successfully ingested: {filename} (id={doc_id}, {len(chunks)} chunks)")
                return {
                    "id": doc_id,
                    "filename": filename,
                    "status": "ready",
                    "error": None,
                }
                
            except Exception as e:
                logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
                doc.status = "failed"
                doc.error = str(e)[:500]
                db.commit()
                return {
                    "id": doc_id,
                    "filename": filename,
                    "status": "failed",
                    "error": str(e),
                }
                
    except Exception as e:
        logger.error(f"Failed to start ingestion for {filename}: {e}", exc_info=True)
        return {
            "id": None,
            "filename": filename,
            "status": "failed",
            "error": str(e),
        }


def ingest_workspace(workspace_slug: str) -> list:
    """
    Ingest all PDFs in a workspace's docs directory.
    
    Args:
        workspace_slug: Workspace identifier
        
    Returns:
        List of ingestion results
    """
    docs_dir = get_docs_dir(workspace_slug)
    
    if not docs_dir.exists():
        logger.warning(f"Documents directory not found: {docs_dir}")
        return []
    
    pdf_files = list(docs_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {workspace_slug}")
    
    results = []
    for pdf_file in pdf_files:
        result = ingest_file(workspace_slug, pdf_file)
        results.append(result)
    
    return results
