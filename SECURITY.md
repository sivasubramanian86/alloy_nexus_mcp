# Security Policy: QuerySage - Pharma Inventory Intelligence

## 🚥 Governance Overview
This repository enforces high-standard security protocols for deploying [**Generative AI**] in pharmaceutical environments.

## 🛡️ Critical Protections
1.  **VPC-First Architecture**: All database communication (AlloyDB) occurs over [**Private IP**] via Direct VPC Egress from Cloud Run.
2.  **Secret Redaction**: Production credentials (AlloyDB passwords, API keys) are **NEVER** checked into Git. Use Google Cloud [**Secret Manager**] for production deployments.
3.  **GEMINI Safety Filters**: All AI-generated results from the `QuerySage Agent` use standard Vertex AI safety settings for [**Professional / Enterprise**] compliance.

## 🚦 Reporting a Security Bug
Please **DO NOT** open a public issue. We take security seriously. Contact the maintainer [**SIVASUBRAMANIAN**] directly via GitHub DM or private email to report a vulnerability.

## 🚧 Known Hardening Measures
*   **Artifact Isolation**: Containers are scanned for vulnerabilities in Google Artifact Registry.
*   **WAF (Optional)**: In full production, we recommend wrapping the `querysage-ui` in Cloud Armor.

---
**Maintaining Data Integrity for Life-Saving Decisions.** 💎
