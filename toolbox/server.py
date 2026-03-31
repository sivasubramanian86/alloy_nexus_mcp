import asyncio
import os
import json
import structlog
from mcp.server.fastmcp import FastMCP
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Logging
structlog.configure(
    processors=[structlog.processors.JSONRenderer()]
)
logger = structlog.get_logger()

# Config
DATABASE_URL = os.getenv("ALLOYDB_DB_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres")
# Note: For production, use the Secret Manager URL

# Initialize FastMCP
mcp = FastMCP("QuerySage-AlloyDB-Toolbox")

# DB Engine
engine = create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10)

@mcp.tool()
async def get_database_schema() -> str:
    """Returns the DDL/Schema for the pharmaceutical inventory system."""
    schema = """
    Tables:
    - suppliers (supplier_id, name, contact_person, email, phone)
    - wards (ward_id, name, floor_number, head_nurse)
    - drug_inventory (drug_id, name, category, dosage_form, total_stock, reorder_level, price_per_unit, is_controlled, created_at)
    - procurement_orders (order_id, drug_id, supplier_id, quantity, status, order_date, estimated_delivery)
    - inventory_transactions (transaction_id, drug_id, ward_id, quantity_moved, transaction_type, transaction_date)
    """
    return schema

@mcp.tool()
async def convert_nl_to_sql(question: str) -> str:
    """
    Converts a natural language question about drugs or inventory into a PostgreSQL query 
    using the AlloyDB AI 'querysage_pharma_config' configuration.
    """
    try:
        async with engine.connect() as conn:
            # We call the AlloyDB AI translation function
            # This assumes scripts/02_enable_alloydb_ai.sql was run
            stmt = text("SELECT google_ml.predict_row(:config, :input)")
            # In a real AlloyDB setup, the config is registered as a model
            # For this demo, we'll mimic the internal prediction
            res = await conn.execute(stmt, {
                "config": "querysage_pharma_config",
                "input": question
            })
            row = res.fetchone()
            if row:
                # Assuming the format returned by google_ml.predict_row for NL
                return row[0].get("sql", "-- Failed to generate SQL")
            return "-- No result from AlloyDB AI"
    except Exception as e:
        logger.error("mcp_nl_to_sql_error", error=str(e))
        return f"-- Error in translation: {str(e)}"

@mcp.tool()
async def execute_sql_query(sql: str) -> str:
    """Executes a SQL query against AlloyDB and returns rows as a JSON string."""
    # Safety Check: Read-only only
    sql_upper = sql.upper().strip()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
        return json.dumps({"error": "Only SELECT queries are permitted for security."})
    
    try:
        async with engine.connect() as conn:
            res = await conn.execute(text(sql))
            cols = res.keys()
            rows = [dict(zip(cols, row)) for row in res.fetchall()]
            return json.dumps(rows, default=str)
    except Exception as e:
        logger.error("mcp_sql_execution_error", error=str(e))
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    mcp.run()
