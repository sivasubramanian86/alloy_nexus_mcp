"""
QuerySage — FastAPI application entry point.
REST API exposing the NL→SQL→AlloyDB→Gemini pipeline.
"""
from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import get_settings
from database import health_check
from logger import get_logger, configure_logging
from nl_agent import run_nl_query, CURATED_QUERIES

configure_logging()
log = get_logger(__name__)


# ── Lifespan (startup / shutdown hooks) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    log.info("querysage_starting", version="1.0.0", env=settings.environment)
    
    if not settings.project_id:
        log.warning("startup_warning_missing_project_id", msg="Vertex AI features may fail")
    if not settings.alloydb_db_url:
        log.warning("startup_warning_missing_db_url", msg="AlloyDB features will fail")
        
    yield
    log.info("querysage_shutdown")


# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="QuerySage API",
    description=(
        "AI-powered natural language interface for AlloyDB. "
        "Query hospital pharmaceutical inventory using plain English."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────
class NLQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=5,
        max_length=500,
        examples=["Which drugs are below their reorder level?"],
    )


class NLQueryResponse(BaseModel):
    nl_query:       str
    generated_sql:  str | None
    rows:           list[dict[str, Any]]
    row_count:      int
    summary:        str
    source:         str   # "alloydb_ai" | "curated_fallback" | "no_match"
    latency_ms:     int


class HealthResponse(BaseModel):
    status:      str
    alloydb_ok:  bool
    environment: str
    version:     str


# ── Middleware: request timing ────────────────────────────────────────────────
@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    t0 = time.monotonic()
    response = await call_next(request)
    latency_ms = int((time.monotonic() - t0) * 1000)
    response.headers["X-Response-Time-Ms"] = str(latency_ms)
    return response


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health():
    """Liveness/readiness probe — Cloud Run health check endpoint."""
    db_ok = await health_check()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        alloydb_ok=db_ok,
        environment=get_settings().environment,
        version="1.0.0",
    )


@app.post("/query", response_model=NLQueryResponse, tags=["core"])
async def nl_query(req: NLQueryRequest):
    """
    Execute a natural language query against the pharma inventory AlloyDB database.

    Flow:
      1. AlloyDB AI NL → SQL translation (if configured)
      2. Curated SQL fallback (keyword routing)
      3. Gemini 2.5 Flash result summarisation
    """
    try:
        result = await run_nl_query(req.question)
        return NLQueryResponse(**result)
    except Exception as exc:
        log.error("query_endpoint_error", error=str(exc), question=req.question)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/queries/examples", tags=["core"])
async def example_queries() -> dict:
    """Return the 5 curated demo NL queries for the UI suggestion chips."""
    return {
        "examples": [
            {
                "id":       "below_reorder",
                "question": "Which drugs are below their reorder level and need urgent procurement?",
                "category": "Procurement Alerts",
            },
            {
                "id":       "controlled_substances",
                "question": "Show all controlled substances with stock levels and expiry dates",
                "category": "Compliance",
            },
            {
                "id":       "pending_procurement",
                "question": "What is the total value of all pending procurement orders by supplier?",
                "category": "Finance",
            },
            {
                "id":       "top_dispensed",
                "question": "What are the top 10 most dispensed drugs in the last 7 days?",
                "category": "Usage Analytics",
            },
            {
                "id":       "expiring_soon",
                "question": "Which drugs are expiring within 60 days and what is the stock value at risk?",
                "category": "Expiry Management",
            },
        ]
    }


@app.get("/inventory/dashboard", tags=["core"])
async def dashboard_summary():
    """
    Aggregate KPIs for the UI dashboard header:
    - Total drugs tracked
    - Drugs below reorder level
    - Pending procurement orders
    - Controlled substances count
    """
    from database import execute_query
    try:
        kpis = await execute_query("""
            SELECT
                (SELECT COUNT(*) FROM drug_inventory)                           AS total_drugs,
                (SELECT COUNT(*) FROM drug_inventory WHERE current_stock < reorder_level) AS below_reorder,
                (SELECT COUNT(*) FROM procurement_orders WHERE status = 'PENDING')        AS pending_orders,
                (SELECT COUNT(*) FROM drug_inventory WHERE is_controlled = TRUE)          AS controlled_substances,
                (SELECT COUNT(*) FROM drug_inventory
                 WHERE expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
                   AND current_stock > 0)                                       AS expiring_soon
        """)
        return kpis[0] if kpis else {}
    except Exception as exc:
        log.error("dashboard_summary_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=(settings.environment == "development"),
        log_level=settings.log_level.lower(),
    )
