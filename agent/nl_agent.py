"""
QuerySage — Gemini-powered NL query agent.

Pipeline:
  1. Classify intent (is this a valid pharma inventory question?)
  2. Route to AlloyDB AI NL translation OR curated fallback SQL
  3. Execute the query
  4. Summarise results using Gemini 2.5 Flash
"""
from __future__ import annotations

import json
import time
from typing import Any

import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel, Part

from config import get_settings
from database import execute_nl_to_sql, execute_query
from logger import get_logger

log = get_logger(__name__)

# ── Curated fallback queries for the 5 demo NL questions ─────────────────────
# Used when AlloyDB AI NL extension is not yet configured (development mode)
CURATED_QUERIES: dict[str, str] = {
    "below_reorder": """
        SELECT d.drug_name, d.generic_name, d.drug_category,
               d.current_stock, d.reorder_level,
               (d.reorder_level - d.current_stock) AS shortage_quantity,
               s.supplier_name, s.lead_time_days
        FROM drug_inventory d
        JOIN suppliers s ON d.supplier_id = s.supplier_id
        WHERE d.current_stock < d.reorder_level
        ORDER BY (d.reorder_level - d.current_stock) DESC
    """,
    "controlled_substances": """
        SELECT d.drug_name, d.generic_name, d.current_stock,
               d.unit_of_measure, d.expiry_date, d.storage_temp, w.ward_name
        FROM drug_inventory d
        LEFT JOIN wards w ON d.ward_id = w.ward_id
        WHERE d.is_controlled = TRUE
        ORDER BY d.expiry_date
    """,
    "pending_procurement": """
        SELECT s.supplier_name,
               COUNT(po.order_id)       AS pending_orders,
               SUM(po.quantity_ordered) AS total_units_ordered,
               SUM(po.total_cost_usd)   AS total_value_usd
        FROM procurement_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        WHERE po.status = 'PENDING'
        GROUP BY s.supplier_name
        ORDER BY total_value_usd DESC
    """,
    "top_dispensed": """
        SELECT d.drug_name, d.drug_category,
               SUM(it.quantity)  AS total_dispensed,
               COUNT(it.txn_id)  AS dispense_events
        FROM inventory_transactions it
        JOIN drug_inventory d ON it.drug_id = d.drug_id
        WHERE it.txn_type = 'DISPENSE'
          AND it.txn_date >= NOW() - INTERVAL '7 days'
        GROUP BY d.drug_name, d.drug_category
        ORDER BY total_dispensed DESC
        LIMIT 10
    """,
    "expiring_soon": """
        SELECT d.drug_name, d.drug_category, d.current_stock,
               d.unit_of_measure, d.expiry_date,
               (d.expiry_date - CURRENT_DATE)               AS days_to_expiry,
               ROUND(d.current_stock * d.unit_cost_usd, 2)  AS stock_value_at_risk_usd
        FROM drug_inventory d
        WHERE d.expiry_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '60 days'
          AND d.current_stock > 0
        ORDER BY d.expiry_date
    """,
}

# Keyword → curated query key routing
KEYWORD_ROUTER: list[tuple[list[str], str]] = [
    (["reorder", "shortage", "urgent", "below", "low stock"], "below_reorder"),
    (["controlled", "narcotic", "schedule", "morphine", "fentanyl", "ketamine"], "controlled_substances"),
    (["pending", "procurement", "order", "purchase", "supplier", "value"], "pending_procurement"),
    (["dispense", "dispensed", "used", "consumed", "frequent"], "top_dispensed"),
    (["expir", "expire", "expiry", "60 days", "waste", "risk"], "expiring_soon"),
]


def _init_gemini() -> GenerativeModel:
    """Initialize Vertex AI + Gemini model once."""
    settings = get_settings()
    vertexai.init(project=settings.project_id, location=settings.region)
    return GenerativeModel(
        model_name=settings.gemini_model,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 1024,
        },
        system_instruction=(
            "You are a pharmaceutical inventory analyst at a hospital. "
            "Your job is to summarise SQL query results in clear, actionable language "
            "for hospital administrators. Be concise (3-5 bullet points max). "
            "Highlight any critical findings (dangerously low stock, controlled substances, "
            "imminent expiry) in bold. Never hallucinate data not in the results."
        ),
    )


_gemini_model: GenerativeModel | None = None


def get_gemini() -> GenerativeModel:
    global _gemini_model
    if _gemini_model is None:
        _gemini_model = _init_gemini()
    return _gemini_model


def _route_to_fallback(nl_query: str) -> tuple[str | None, str | None]:
    """
    Match the NL query to a curated key using keyword routing.
    Returns (curated_key, sql) or (None, None) if no match.
    """
    q_lower = nl_query.lower()
    for keywords, key in KEYWORD_ROUTER:
        if any(kw in q_lower for kw in keywords):
            return key, CURATED_QUERIES[key]
    return None, None


async def _summarise_with_gemini(nl_query: str, rows: list[dict], generated_sql: str) -> str:
    """Ask Gemini to produce a human-readable summary of the query results."""
    if not rows:
        return "No records matched your query."

    # Truncate to first 20 rows to avoid context bloat
    sample = rows[:20]
    prompt = (
        f"Question asked: {nl_query}\n\n"
        f"SQL executed:\n{generated_sql}\n\n"
        f"Result rows ({len(rows)} total, showing first {len(sample)}):\n"
        f"{json.dumps(sample, default=str, indent=2)}\n\n"
        "Provide a concise, actionable summary for the hospital administrator."
    )

    try:
        model = get_gemini()
        response = model.generate_content(prompt)
        return response.text
    except Exception as exc:
        log.error("gemini_summarise_failed", error=str(exc))
        return f"Query returned {len(rows)} results. (AI summary unavailable: {exc})"


async def run_nl_query(nl_query: str) -> dict[str, Any]:
    """
    Main pipeline:
      1. Try AlloyDB AI NL translation
      2. Fallback to keyword-routed curated SQL if NL not configured
      3. Summarise results with Gemini
    """
    settings = get_settings()
    t0 = time.monotonic()
    source = "alloydb_ai"

    log.info("nl_query_received", query=nl_query)

    # ── Attempt 1: AlloyDB AI NL Translation ─────────────────────────────────
    result = await execute_nl_to_sql(nl_query, settings.nl_config_name)

    # ── Attempt 2: Curated SQL Fallback ──────────────────────────────────────
    if result.get("error") or not result.get("generated_sql"):
        _, fallback_sql = _route_to_fallback(nl_query)
        if fallback_sql:
            source = "curated_fallback"
            rows = await execute_query(fallback_sql)
            result = {
                "generated_sql": fallback_sql.strip(),
                "rows":          rows,
                "row_count":     len(rows),
            }
        else:
            source = "no_match"
            return {
                "nl_query":      nl_query,
                "generated_sql": None,
                "rows":          [],
                "row_count":     0,
                "summary":       (
                    "I couldn't map your question to a known query pattern. "
                    "Try asking about: stock levels, controlled substances, pending orders, "
                    "dispensing history, or expiring drugs."
                ),
                "source":        source,
                "latency_ms":    int((time.monotonic() - t0) * 1000),
            }

    # ── Step 3: Gemini summarisation ─────────────────────────────────────────
    summary = await _summarise_with_gemini(
        nl_query,
        result["rows"],
        result["generated_sql"],
    )

    latency_ms = int((time.monotonic() - t0) * 1000)
    log.info(
        "nl_query_complete",
        source=source,
        row_count=result["row_count"],
        latency_ms=latency_ms,
    )

    return {
        "nl_query":      nl_query,
        "generated_sql": result["generated_sql"],
        "rows":          result["rows"],
        "row_count":     result["row_count"],
        "summary":       summary,
        "source":        source,
        "latency_ms":    latency_ms,
    }
