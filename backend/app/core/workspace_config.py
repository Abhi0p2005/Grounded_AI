"""Workspace configuration loader and validator."""
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, ValidationError

from app.settings import settings


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""

    top_k: int = Field(default=5, ge=1, le=20)
    min_score: float = Field(default=0.35, ge=0.0, le=1.0)
    hybrid: bool = Field(default=False)


class LLMConfig(BaseModel):
    """LLM configuration."""

    model: str = Field(default="gemini-1.5-flash")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=700, ge=100, le=4000)


class WorkspaceConfig(BaseModel):
    """Main workspace configuration."""

    slug: str
    name: str
    description: str
    assistant_persona: str
    language: str = Field(default="en")
    retrieval: RetrievalConfig
    llm: LLMConfig
    history_turns: int = Field(default=4, ge=0, le=20)
    handoff_message: str


class PIIConfig(BaseModel):
    """PII masking configuration."""

    enabled: bool = Field(default=True)
    patterns: Dict[str, str] = Field(default_factory=dict)


class InputGuardrailsConfig(BaseModel):
    """Input guardrails configuration."""

    blocked_topics: List[str] = Field(default_factory=list)
    injection_heuristics: List[str] = Field(default_factory=list)
    llm_check: bool = Field(default=False)


class OutputGuardrailsConfig(BaseModel):
    """Output guardrails configuration."""

    forbidden_phrases: List[str] = Field(default_factory=list)
    require_citation_for_knowledge: bool = Field(default=True)
    llm_auditor: bool = Field(default=True)
    auditor_fail_open: bool = Field(default=False)


class GuardrailsConfig(BaseModel):
    """Guardrails configuration."""

    pii: PIIConfig
    input: InputGuardrailsConfig
    output: OutputGuardrailsConfig
    safe_fallback_message: str


class ToolParameterSchema(BaseModel):
    """Tool parameter JSON schema."""

    type: str
    properties: Dict[str, Any]
    required: List[str] = Field(default_factory=list)


class ToolConfig(BaseModel):
    """Single tool configuration."""

    name: str
    description: str
    import_path: str
    parameters: ToolParameterSchema


class ToolsConfig(BaseModel):
    """Tools configuration."""

    tools: List[ToolConfig] = Field(default_factory=list)


class EvalCase(BaseModel):
    """Single evaluation case."""

    id: str
    question: str
    expected_source: Optional[str] = None
    reference_answer: Optional[str] = None
    expected_tool: Optional[str] = None
    expected_tool_args: Optional[Dict[str, Any]] = None
    should_refuse: bool
    category: str


class EvalConfig(BaseModel):
    """Evaluation configuration."""

    cases: List[EvalCase] = Field(default_factory=list)


def load_yaml_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse a YAML file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")


def compute_config_hash(workspace_dir: Path) -> str:
    """Compute hash of all config files for cache invalidation."""
    config_files = ["workspace.yaml", "guardrails.yaml", "tools.yaml"]
    hasher = hashlib.sha256()
    
    for filename in sorted(config_files):
        file_path = workspace_dir / filename
        if file_path.exists():
            with open(file_path, "rb") as f:
                hasher.update(f.read())
    
    return hasher.hexdigest()[:16]


def load_workspace_config(slug: str) -> WorkspaceConfig:
    """Load and validate workspace configuration."""
    workspace_dir = settings.workspaces_path / slug
    
    if not workspace_dir.exists():
        raise FileNotFoundError(f"Workspace not found: {slug}")
    
    config_file = workspace_dir / "workspace.yaml"
    data = load_yaml_file(config_file)
    
    try:
        return WorkspaceConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid workspace.yaml for '{slug}': {e}")


def load_guardrails_config(slug: str) -> GuardrailsConfig:
    """Load and validate guardrails configuration."""
    workspace_dir = settings.workspaces_path / slug
    config_file = workspace_dir / "guardrails.yaml"
    data = load_yaml_file(config_file)
    
    try:
        return GuardrailsConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid guardrails.yaml for '{slug}': {e}")


def load_tools_config(slug: str) -> ToolsConfig:
    """Load and validate tools configuration."""
    workspace_dir = settings.workspaces_path / slug
    config_file = workspace_dir / "tools.yaml"
    data = load_yaml_file(config_file)
    
    try:
        return ToolsConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid tools.yaml for '{slug}': {e}")


def load_eval_config(slug: str) -> EvalConfig:
    """Load and validate eval configuration."""
    workspace_dir = settings.workspaces_path / slug
    config_file = workspace_dir / "eval.yaml"
    data = load_yaml_file(config_file)
    
    try:
        return EvalConfig(**data)
    except ValidationError as e:
        raise ValueError(f"Invalid eval.yaml for '{slug}': {e}")


def get_workspace_dir(slug: str) -> Path:
    """Get workspace directory path."""
    return settings.workspaces_path / slug


def get_docs_dir(slug: str) -> Path:
    """Get workspace documents directory."""
    return get_workspace_dir(slug) / "docs"
