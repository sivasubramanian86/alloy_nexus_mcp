#!/usr/bin/env bash
# =============================================================================
# QuerySage: AlloyDB Initialization Script
# Run from Cloud Shell — connects via Proxy and seeds the database.
# =============================================================================
set -e

# Configuration
PROJECT_ID="genai-apac-2026-491004"
REGION="us-central1"
CLUSTER_ID="querysage-cluster"
INSTANCE_ID="querysage-primary"
DB_NAME="pharma_inventory"
DB_PASS="[DB_PASSWORD_FROM_SECRET_MANAGER]"

echo "=== QuerySage Database Initialization ==="

# 1. Download AlloyDB Auth Proxy
echo "[1/4] Downloading AlloyDB Auth Proxy..."
if [ ! -f ./alloydb-auth-proxy ]; then
  curl -L https://storage.googleapis.com/alloydb-auth-proxy/v1.11.0/alloydb-auth-proxy.linux.amd64 -o alloydb-auth-proxy
  chmod +x alloydb-auth-proxy
fi

# 2. Get Full Instance Path
INSTANCE_PATH="projects/${PROJECT_ID}/locations/${REGION}/clusters/${CLUSTER_ID}/instances/${INSTANCE_ID}"

# 3. Start Proxy in the background
echo "[2/4] Starting Proxy for $INSTANCE_PATH..."
./alloydb-auth-proxy "$INSTANCE_PATH" --port 5432 &
PROXY_PID=$!

# Wait for proxy to be ready
echo "Waiting 10s for proxy to stabilize..."
sleep 10

# 4. Execute SQL Setup
echo "[3/4] Running SQL Initialization..."
export PGPASSWORD="$DB_PASS"

# Create Database (ignore error if already exists)
psql -h localhost -U postgres -c "CREATE DATABASE $DB_NAME;" || true

# Run Schema and Seed
echo "Seeding schema and pharmaceutical inventory data..."
psql -h localhost -U postgres -d "$DB_NAME" -f scripts/01_setup_alloydb.sql

# Enable AlloyDB AI
echo "Configuring AlloyDB AI (NL-to-SQL extensions)..."
psql -h localhost -U postgres -d "$DB_NAME" -f scripts/02_enable_alloydb_ai.sql

echo "[4/4] Initialization Complete."

# Cleanup
echo "Cleaning up..."
kill $PROXY_PID || true
unset PGPASSWORD

echo "=== Done! Your AlloyDB is ready. ==="
