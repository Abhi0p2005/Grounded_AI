# Architectural Decisions Log

> One-line decisions made during implementation. Date format: YYYY-MM-DD

## 2026-10-24

1. **LLM Provider**: Google AI Studio (Gemini) instead of Groq - free tier, good performance, structured output support
2. **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, 80MB) - smaller than BGE, faster CPU inference
3. **Token Counter**: `tiktoken` cl100k_base approximation - good enough for ~500 token chunks
4. **Schema Management**: Direct SQL (`schema.sql`) instead of Alembic - simpler for 5 tables, idempotent on startup
5. **Cache Key Strategy**: Include `config_hash` in Redis key - config changes automatically invalidate cache
6. **LangGraph**: Full state machine for agent flow - clear debugging, conditional edges for routing
