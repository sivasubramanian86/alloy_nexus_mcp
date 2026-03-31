import asyncio
import os
import json
from google import adk
from .config import settings
from .logger import structlog_logger
from google.generativeai import GenerativeModel

# MCP Server URL for the Toolbox
TOOLBOX_MCP_URL = os.getenv("TOOLBOX_MCP_URL", "http://localhost:8081/mcp")

logger = structlog_logger.get_logger()

# Agentic Logic using Google ADK
async def run_querysage_agent(user_question: str):
    """
    Core ADK Agent flow for Track 3:
    1. Initialize the ADK Agent with AlloyDB Toolbox tools.
    2. Agent decides to:
       - Get database schema (if needed context).
       - Convert NL to SQL (using AlloyDB AI).
       - Execute SQL to get data.
    3. Return structured data + natural language summary.
    """
    
    # Define tool functions that the ADK Agent can use
    # In a real MCP setup, these are provided by the MCP client
    # For this hackathon demo, we define them to bridge to the Toolbox
    
    async def fetch_alloydb_sql(sql: str):
        # Implementation to call the Toolbox
        # For simplicity, we directly call the db module since it's the same service/project
        from .database import execute_query
        return await execute_query(sql)

    async def translate_nl(question: str):
        from .database import translate_nl_to_sql
        return await translate_nl_to_sql(question)

    # 1. Initialize Gemini with Tools
    llm = GenerativeModel(model_name=settings.GEMINI_MODEL)
    
    # 2. Agent Prompt Template
    sys_prompt = f"""
    You are QuerySage, an expert pharmaceutical inventory assistant.
    Your objective is to answer the User Question by querying the AlloyDB database.
    
    Rules:
    1. Check if the question is an inventory/drug query.
    2. Use 'translate_nl' to convert the user's natural language into a PostgreSQL query.
    3. Use 'fetch_alloydb_sql' to execute that query.
    4. If 'translate_nl' fails or looks wrong, you can refine the query using your own knowledge of the schema.
    
    Schema context: {settings.PROJECT_NAME} Pharma Inventory (drugs, suppliers, orders, transactions).
    """

    # 3. Running the flow (Simplified Chain an Agent would do)
    # Note: ADK uses a task/plan loop usually.
    
    # Step A: Translate (Internal tool call or model logic)
    sql_result = await translate_nl(user_question)
    
    # Step B: Execute
    db_rows = await fetch_alloydb_sql(sql_result)
    
    # Step C: Summarize (Generative logic)
    context = json.dumps(db_rows, default=str)
    summary_prompt = f"Summarize this inventory data for the question: {user_question}\nData: {context}"
    summary = llm.generate_content(summary_prompt).text
    
    return {
        "question": user_question,
        "translated_sql": sql_result,
        "rows": db_rows,
        "summary": summary,
        "source": "alloydb_ai_agent"
    }
