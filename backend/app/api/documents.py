"""Document management endpoints."""
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import get_db
from app.ingestion.pipeline import ingest_file
from app.models import Chunk, Document, Workspace
from app.schemas import DocumentInfo, DocumentUploadResponse
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{slug}/documents", response_model=list[DocumentInfo])
def list_documents(slug: str, db: Session = Depends(get_db)):
    """List all documents in a workspace."""
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    
    documents = (
        db.query(Document)
        .filter(Document.workspace_id == workspace.id)
        .order_by(Document.created_at.desc())
        .all()
    )
    
    result = []
    for doc in documents:
        chunk_count = (
            db.query(func.count(Chunk.id))
            .filter(Chunk.document_id == doc.id)
            .scalar()
        )
        
        result.append(
            DocumentInfo(
                id=doc.id,
                filename=doc.filename,
                status=doc.status,
                page_count=doc.page_count,
                chunk_count=chunk_count or 0,
                created_at=doc.created_at,
                error=doc.error,
            )
        )
    
    return result


@router.post("/{slug}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    slug: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document to the workspace."""
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save uploaded file temporarily
    temp_dir = Path(settings.workspaces_path) / slug / "docs"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename
    
    try:
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # Ingest the file
        result = ingest_file(slug, temp_path)
        
        return DocumentUploadResponse(
            id=result["id"],
            filename=result["filename"],
            status=result["status"],
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{slug}/documents/{doc_id}")
def delete_document(slug: str, doc_id: int, db: Session = Depends(get_db)):
    """Delete a document and its chunks."""
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    
    document = (
        db.query(Document)
        .filter(
            Document.id == doc_id,
            Document.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    db.delete(document)
    db.commit()
    
    return {"status": "deleted", "id": doc_id}


@router.get("/{slug}/chunks/{chunk_id}")
def get_chunk(slug: str, chunk_id: int, db: Session = Depends(get_db)):
    """Get chunk details for citation panel."""
    workspace = db.query(Workspace).filter(Workspace.slug == slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    
    chunk = (
        db.query(Chunk)
        .join(Document)
        .filter(
            Chunk.id == chunk_id,
            Chunk.workspace_id == workspace.id,
        )
        .first()
    )
    
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    return {
        "id": chunk.id,
        "text": chunk.text,
        "document": chunk.document.filename,
        "page": chunk.page_number,
        "chunk_index": chunk.chunk_index,
    }
