# 💊 QuerySage: AI-Powered AlloyDB Pharmaceutical Agent

[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud-Run-4285F4?logo=google-cloud&logoColor=white)](#)
[![AlloyDB AI](https://img.shields.io/badge/AlloyDB-AI--Ready-blue?logo=postgresql&logoColor=white)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](#)
[![Gemini 2.0](https://img.shields.io/badge/Gemini-2.0%20Flash-magenta?logo=google-gemini&logoColor=white)](#)

> **Track 3 Hackathon Entry:** Building AI-powered applications using AI-ready databases like AlloyDB.

**QuerySage** is an intelligent pharmaceutical inventory management agent that enables hospital staff to interact with complex drug data using natural language. Built on **AlloyDB for PostgreSQL**, it leverages **AlloyDB AI**'s native NL-to-SQL capabilities and the **Google Agent Development Kit (ADK)** to bridge raw data and actionable medical insights.

### 🔗 Live Project Dashboard
- **Frontend UI:** [https://querysage-ui-967518492968.us-central1.run.app](https://querysage-ui-967518492968.us-central1.run.app)
- **Backend API:** [https://querysage-agent-967518492968.us-central1.run.app](https://querysage-agent-967518492968.us-central1.run.app)

---

## 🏗 System Architecture

The project follows a 3-tier, cloud-native architecture:

1.  **Frontend (React/HTML/JS):** A premium, glassmorphic dark-mode dashboard for real-time inventory analytics, query input, and data visualization.
2.  **Agent Tier (FastAPI + ADK):** 
    -   An AI Agent orchestrated via **Google ADK** and **Gemini 2.5 Flash**.
    -   An **MCP (Model Context Protocol) Toolbox** that exposes AlloyDB's capabilities as tools.
3.  **Data Tier (AlloyDB AI):** 
    -   Fully managed PostgreSQL cluster with the `google_ml_integration` extension.
    -   A specialized `querysage_pharma_config` to translate pharma-specific NL phrases into optimized SQL.

---

## ⚡ Key Features

-   **Natural Language to SQL:** Hospital admins can ask, *"Which life-saving drugs are below reorder levels?"* or *"Show me the distribution of controlled substances across wards."*
-   **AlloyDB AI Integration:** Native database-level translation for high performance and context-aware querying.
-   **Automated Summarization:** Gemini 2.5 Flash analyzes SQL results to provide human-readable summaries and clinical recommendations.
-   **Real-time Analytics:** A KPI dashboard tracking drug shortages, expiring medications, and pending orders.
-   **Safe Querying:** Strictly enforced `SELECT-only` policy for NL-translated queries to prevent SQL injection or data mutation.

---

## 📂 Repository Structure

```text
.
├── agent/            # FastAPI Backend & ADK Agent
├── frontend/         # Premium UI & Business Logic
├── toolbox/          # MCP Server (AlloyDB Tools)
├── scripts/          # IaC & Database Setup
│   ├── 01_setup_alloydb.sql      # Schema & Seed Data
│   ├── 02_enable_alloydb_ai.sql   # AlloyDB AI NL Config
│   └── 03_provision_alloydb.sh    # GCP Provisioning (IaC)
└── .github/          # CI/CD Workflow (Cloud Run)
```

---

## 🚀 Quick Start

### 1. Provision Infrastructure
Run the provisioning script from Google Cloud Shell:
```bash
./scripts/03_provision_alloydb.sh
```

### 2. Configure Database
Apply the SQL files to your AlloyDB instance:
```bash
# Apply schema
psql -h <ALLOYDB_IP> -U postgres -d postgres -f scripts/01_setup_alloydb.sql
# Apply AI extension and config
psql -h <ALLOYDB_IP> -U postgres -d postgres -f scripts/02_enable_alloydb_ai.sql
```

### 3. Deploy to Cloud Run
The project is containerized and ready for deployment. Use the provided GitHub Actions workflow or run:
```bash
gcloud run deploy querysage-agent --source ./agent --region us-central1
gcloud run deploy querysage-ui --source ./frontend --region us-central1
```

---

## 🧪 Example Queries
-   "List all drugs that are expiring in the next 30 days."
-   "Show me the total stock value per drug category."
-   "Find the supplier for 'Insulin Aspart' and the pending orders."
-   "What is the distribution of 'Ativan' across all hospital wards?"

---

## 🛠 Tech Stack
-   **Database:** AlloyDB for PostgreSQL, AlloyDB AI (Model Integration)
-   **Orchestration:** Google ADK, MCP (Model Context Protocol)
-   **Models:** Gemini 2.5 Flash, NL-to-SQL (AlloyDB ML)
-   **Backend:** Python 3.12, FastAPI, SQLAlchemy, Asyncpg
-   **Frontend:** Nginx, Vanilla JS, HTML5, CSS3 (Glassmorphism)
-   **Deployment:** Google Cloud Run, Artifact Registry, Secret Manager

---

## 🤝 Contributing
This was built for the **Gen AI APAC Hackathon 2026**.
Developer: **Antigravity (AI)**
Lead Architect: **User**
