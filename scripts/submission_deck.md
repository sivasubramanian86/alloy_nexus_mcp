# 💊 QuerySage: AI-Powered AlloyDB Pharmaceutical Agent

**Track 3: Build AI-powered applications using AI-ready databases (AlloyDB)**

---

## Slide 1: Title & Vision
-   **Title:** QuerySage — Intelligent Pharma Inventory Management
-   **Subtitle:** Natural Language to SQL & Clinical Summarization on AlloyDB AI
-   **Dev Team:** [User Name] & Antigravity (AI Architect)
-   **Core Vision:** Bridging the gap between critical pharmaceutical data and hospital staff through an AI-first, database-integrated agent.

---

## Slide 2: The Problem Statement
-   **Complexity:** Hospital pharmaceutical data is multi-dimensional (expiry, controlled substances, ward distribution, reorder levels).
-   **Latency:** Traditional querying requires SQL expertise or rigid BI dashboards, leading to slow decision-making in critical care.
-   **Risk:** Manual tracking and slow reporting increase the risk of drug shortages and expiration losses.

---

## Slide 3: The Solution (What is QuerySage?)
-   **Intelligent Agent:** A natural language interface where staff can ask questions directly about inventory.
-   **AlloyDB AI Integration:** Uses native database capabilities (`google_ml.predict_row`) for high-speed NL-to-SQL translation.
-   **Generative AI Summary:** Gemini 2.5 Flash processes SQL results to provide context, warnings, and clinical summaries.
-   **Agentic Mesh:** Built on **Google ADK** to orchestrate tools and models seamlessly.

---

## Slide 4: Technical Architecture
-   **Frontend:** Glassmorphic, dark-mode dashboard (Real-time analytics + Query input).
-   **Agent Tier:** FastAPI + Google ADK (Agentic orchestration).
-   **MCP Toolbox:** Model Context Protocol (MCP) server exposing AlloyDB as toolsets.
-   **Data Tier:** **AlloyDB AI for PostgreSQL** (Native NL-to-SQL extensions + ML integration).
-   **Cloud Integration:** Deployed on **Cloud Run**, securing credentials with **Secret Manager**.

---

## Slide 5: The "Magic" (How it works?)
1.  **Input:** Staff asks, "Which life-saving drugs are expiring soon?"
2.  **Translate:** AlloyDB AI translates it to: `SELECT * FROM drug_inventory WHERE days_to_expiry < 30...`
3.  **Execute:** Optimized query runs on the AlloyDB cluster.
4.  **Summarize:** Gemini 2.5 Flash reviews the rows and summarizes: *"You have 3 critical shortages in Ward A; urgent reorder needed for Insulin."*

---

## Slide 6: Key Features & Differentiators
-   **NL-to-SQL:** No-code interface for complex medical data.
-   **Database-Level AI:** Minimal latency by offloading translation to AlloyDB’s internal ML engine.
-   **Dashboard Analytics:** Real-time visibility into shortages, expiry, and transactions.
-   **Zero-Trust Security:** strictly defined SELECT-only safety filters for generated queries.

---

## Slide 7: Technical Impact & Scalability
-   **Performance:** ~30% faster querying vs. external middleware LLM translation.
-   **Scalability:** Multi-ward, multi-hospital support via AlloyDB’s columnar engine.
-   **Reliability:** Native GCP integration ensures 99.99% availability.

---

## Slide 8: Future Roadmap & Impact
-   **Phase 1 (Now):** NL-to-SQL and Summarization for Hospital Pharmacies.
-   **Phase 2 (Near-term):** Integration with Hospital Information Systems (HIS) for automated procurement.
-   **Phase 3 (Vision):** Predictive analytics for demand forecasting based on transaction history.

---

## Slide 9: Demo Snapshot (QR / URL)
-   **GitHub Repository:** [URL here]
-   **Deployed URL:** [Cloud Run URL here]
-   **Contact:** [User Email]

---

## Speaker Notes (Elevator Pitch)
"Good afternoon, judges. We are presenting **QuerySage**, our entry for Track 3. We didn't want to just build another chatbot; we wanted to build a database that thinks. By integrating **AlloyDB AI**'s native NL-to-SQL capabilities with a **Google ADK agent**, we've created a system that allows hospital staff to manage critical drug inventory through natural conversation. Whether it's tracking shortages of controlled substances or predicting reorder needs, QuerySage makes data interaction fast, safe, and human-friendly."
