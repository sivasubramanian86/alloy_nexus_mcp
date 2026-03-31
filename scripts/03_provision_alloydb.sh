#!/usr/bin/env bash
# =============================================================================
# QuerySage: AlloyDB Instance Provisioning Script
# Run from Cloud Shell — sets up AlloyDB cluster, instance, and DB
# =============================================================================
set -euo pipefail

# --------------------------------------------------------------------------
# CONFIG — edit before running
# --------------------------------------------------------------------------
export PROJECT_ID="genai-apac-2026-491004"
export REGION="us-central1"
export CLUSTER_ID="querysage-cluster"
export INSTANCE_ID="querysage-primary"
export DB_NAME="pharma_inventory"
export DB_USER="querysage_admin"
export DB_PASSWORD="$(openssl rand -base64 32)"  # auto-generated
export NETWORK="default"

echo "=== QuerySage AlloyDB Setup ==="
echo "Project : $PROJECT_ID"
echo "Region  : $REGION"
echo "Cluster : $CLUSTER_ID"

# --------------------------------------------------------------------------
# Step 1: Enable required APIs
# --------------------------------------------------------------------------
gcloud services enable \
    alloydb.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudrun.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project="$PROJECT_ID"

echo "[1/7] APIs enabled."

# --------------------------------------------------------------------------
# Step 2: Create AlloyDB Cluster
# --------------------------------------------------------------------------
gcloud alloydb clusters create "$CLUSTER_ID" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --password="$DB_PASSWORD" \
    --network="$NETWORK"

echo "[2/7] AlloyDB cluster created."

# --------------------------------------------------------------------------
# Step 3: Create Primary Read-Write Instance
# --------------------------------------------------------------------------
gcloud alloydb instances create "$INSTANCE_ID" \
    --cluster="$CLUSTER_ID" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --instance-type=PRIMARY \
    --cpu-count=4

echo "[3/7] AlloyDB primary instance created (wait ~5 minutes for READY status)."

# --------------------------------------------------------------------------
# Step 4: Get the AlloyDB Private IP
# --------------------------------------------------------------------------
ALLOYDB_IP=$(gcloud alloydb instances describe "$INSTANCE_ID" \
    --cluster="$CLUSTER_ID" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --format="value(ipAddress)")

echo "[4/7] AlloyDB IP: $ALLOYDB_IP"

# --------------------------------------------------------------------------
# Step 5: Store secrets in Secret Manager
# --------------------------------------------------------------------------
echo -n "$DB_PASSWORD" | gcloud secrets create querysage-db-password \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID"

echo -n "postgresql+psycopg2://${DB_USER}:${DB_PASSWORD}@${ALLOYDB_IP}:5432/${DB_NAME}" \
    | gcloud secrets create querysage-db-url \
    --data-file=- \
    --replication-policy="automatic" \
    --project="$PROJECT_ID"

echo "[5/7] Secrets stored in Secret Manager."

# --------------------------------------------------------------------------
# Step 6: Grant AlloyDB SA access to Vertex AI (for AlloyDB AI feature)
# --------------------------------------------------------------------------
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
ALLOYDB_SA="service-${PROJECT_NUMBER}@gcp-sa-alloydb.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${ALLOYDB_SA}" \
    --role="roles/aiplatform.user"

echo "[6/7] Vertex AI access granted to AlloyDB SA: $ALLOYDB_SA"

# --------------------------------------------------------------------------
# Step 7: Create the database and run schema SQL
# --------------------------------------------------------------------------
echo "[7/7] Run the following commands to initialize the database:"
echo ""
echo "  # Connect to AlloyDB via Cloud SQL Proxy or psql from Cloud Shell:"
echo "  psql -h $ALLOYDB_IP -U $DB_USER -c 'CREATE DATABASE $DB_NAME;'"
echo "  psql -h $ALLOYDB_IP -U $DB_USER -d $DB_NAME -f scripts/01_setup_alloydb.sql"
echo "  psql -h $ALLOYDB_IP -U $DB_USER -d $DB_NAME -f scripts/02_enable_alloydb_ai.sql"
echo ""
echo "=== Setup Complete ==="
echo "DB URL: postgresql+psycopg2://${DB_USER}:*****@${ALLOYDB_IP}:5432/${DB_NAME}"
echo "IMPORTANT: Save the DB password from Secret Manager before closing this session."
