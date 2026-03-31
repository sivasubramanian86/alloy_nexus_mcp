"""
QuerySage Agent — settings and environment configuration.
All secrets are read from environment variables or GCP Secret Manager.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings — sourced from .env (local) or Secret Manager (Cloud Run)."""

    # ── GCP / Vertex AI ──────────────────────────────────────────────────────
    project_id: str | None   = Field(None,   env="PROJECT_ID")
    region:     str          = Field("us-central1", env="REGION")
    gemini_model: str        = Field("gemini-2.0-flash-exp", env="GEMINI_MODEL")

    # ── AlloyDB connection ───────────────────────────────────────────────────
    alloydb_db_url: str | None = Field(None, env="ALLOYDB_DB_URL")
    # Format: postgresql+psycopg2://user:password@<private_ip>:5432/pharma_inventory

    # ── AlloyDB AI NL config name ─────────────────────────────────────────────
    nl_config_name: str      = Field("querysage_pharma_config", env="NL_CONFIG_NAME")

    # ── Application ─────────────────────────────────────────────────────────
    environment: str         = Field("production", env="ENVIRONMENT")
    log_level: str           = Field("INFO",        env="LOG_LEVEL")
    port: int                = Field(8080,           env="PORT")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton — avoids re-reading env on every request."""
    return Settings()
