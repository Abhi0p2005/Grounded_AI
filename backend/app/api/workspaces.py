"""Workspace management endpoints."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.workspace_config import (
    compute_config_hash,
    get_workspace_dir,
    load_guardrails_config,
    load_tools_config,
    load_workspace_config,
)
from app.db import get_db
from app.models import Chunk, Document, Workspace
from app.schemas import WorkspaceDetail, WorkspaceInfo
from app.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[WorkspaceInfo])
def list_workspaces(db: Session = Depends(get_db)):
    """List all workspaces with document/chunk counts."""
    workspaces = db.query(Workspace).all()
    
    result = []
    for ws in workspaces:
        doc_count = db.query(func.count(Document.id)).filter(Document.workspace_id == ws.id).scalar()
        chunk_count = db.query(func.count(Chunk.id)).filter(Chunk.workspace_id == ws.id).scalar()
        
        result.append(
            WorkspaceInfo(
                slug=ws.slug,
                name=ws.name,
                doc_count=doc_count or 0,
                chunk_count=chunk_count or 0,
            )
        )
    
    return result


@router.post("/reload")
def reload_workspaces(db: Session = Depends(get_db)):
    """Reload all workspace configurations from disk."""
    workspaces_path = settings.workspaces_path
    
    if not workspaces_path.exists():
        raise HTTPException(status_code=404, detail="Workspaces directory not found")
    
    loaded = []
    
    for workspace_dir in workspaces_path.iterdir():
        if not workspace_dir.is_dir():
            continue
        
        slug = workspace_dir.name
        config_file = workspace_dir / "workspace.yaml"
        
        if not config_file.exists():
            logger.warning(f"No workspace.yaml in {slug}, skipping")
            continue
        
        try:
            config = load_workspace_config(slug)
            config_hash = compute_config_hash(workspace_dir)
            
            # Upsert workspace
            ws = db.query(Workspace).filter(Workspace.slug == slug).first()
            if ws:
                ws.name = config.name
                ws.config_hash = config_hash
            else:
                ws = Workspace(
                    slug=slug,
                    name=config.name,
                    config_hash=config_hash,
                )
                db.add(ws)
            
            db.commit()
            loaded.append(slug)
            logger.info(f"Loaded workspace: {slug}")
            
        except Exception as e:
            logger.error(f"Failed to load workspace {slug}: {e}")
            continue
    
    return {"loaded": loaded, "count": len(loaded)}


@router.get("/{slug}", response_model=WorkspaceDetail)
def get_workspace(slug: str):
    """Get detailed workspace configuration."""
    try:
        ws_config = load_workspace_config(slug)
        gr_config = load_guardrails_config(slug)
        tools_config = load_tools_config(slug)
        
        return WorkspaceDetail(
            slug=ws_config.slug,
            name=ws_config.name,
            description=ws_config.description,
            tools=[t.name for t in tools_config.tools],
            retrieval_settings={
                "top_k": ws_config.retrieval.top_k,
                "min_score": ws_config.retrieval.min_score,
                "hybrid": ws_config.retrieval.hybrid,
            },
            guardrails_enabled={
                "pii": gr_config.pii.enabled,
                "input_llm_check": gr_config.input.llm_check,
                "output_auditor": gr_config.output.llm_auditor,
            },
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workspace not found: {slug}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
