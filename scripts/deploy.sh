#!/bin/bash
# =============================================================================
# deploy.sh - One-command deploy for the Parquet File Inspector
#
# Prerequisites:
#   - AWS CLI configured with credentials
#   - Node.js >= 18
#   - CDK bootstrapped in the target account/region
#
# Usage:
#   ./scripts/deploy.sh
#
# What it does:
#   1. Downloads DuckDB-WASM binaries (if not present)
#   2. Generates sample data (if not present)
#   3. Installs CDK dependencies
#   4. Deploys the CDK stack
#   5. Fixes WASM MIME types in S3
# =============================================================================

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🗂️  Parquet File Inspector - Deploy"
echo "==================================="

# --- Step 1: Download DuckDB WASM binaries ---
DUCKDB_DIR="$PROJECT_DIR/src/frontend/duckdb"
DUCKDB_VERSION="1.29.0"
CDN="https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${DUCKDB_VERSION}/dist"

if [ ! -f "$DUCKDB_DIR/duckdb-eh.wasm" ]; then
  echo "📦 Downloading DuckDB-WASM binaries (v${DUCKDB_VERSION})..."
  curl -sL "$CDN/duckdb-eh.wasm" -o "$DUCKDB_DIR/duckdb-eh.wasm"
  curl -sL "$CDN/duckdb-mvp.wasm" -o "$DUCKDB_DIR/duckdb-mvp.wasm"
  echo "   ✓ Downloaded (~73MB total)"
else
  echo "✓ DuckDB-WASM binaries already present"
fi

# --- Step 2: Generate sample data ---
SAMPLE="$PROJECT_DIR/sample-data/iot_sensors.parquet"
if [ ! -f "$SAMPLE" ]; then
  echo "📊 Generating sample data..."
  python3 "$SCRIPT_DIR/generate_sample_data.py" "$SAMPLE"
else
  echo "✓ Sample data already present ($(du -h "$SAMPLE" | cut -f1))"
fi

# --- Step 3: Install CDK dependencies ---
echo "📦 Installing CDK dependencies..."
cd "$PROJECT_DIR/infrastructure"
npm install --quiet

# --- Step 4: Deploy ---
echo "🚀 Deploying to AWS..."
export CDK_DEFAULT_ACCOUNT="${CDK_DEFAULT_ACCOUNT:-$(aws sts get-caller-identity --query Account --output text)}"
export CDK_DEFAULT_REGION="${CDK_DEFAULT_REGION:-$(aws configure get region)}"
export AWS_REGION="$CDK_DEFAULT_REGION"
export AWS_DEFAULT_REGION="$CDK_DEFAULT_REGION"

npx cdk deploy --require-approval never --outputs-file outputs.json

# --- Step 5: Fix WASM MIME types ---
# S3 may serve .wasm as binary/octet-stream; browsers require application/wasm
BUCKET=$(jq -r '.ParquetInspectorStack.BucketName' outputs.json)
DIST_ID=$(jq -r '.ParquetInspectorStack.DistributionId' outputs.json)
URL=$(jq -r '.ParquetInspectorStack.WebsiteURL' outputs.json)

echo "🔧 Fixing WASM MIME types..."
aws s3 cp "s3://$BUCKET/duckdb/duckdb-eh.wasm" "s3://$BUCKET/duckdb/duckdb-eh.wasm" \
  --content-type "application/wasm" --metadata-directive REPLACE --region "$CDK_DEFAULT_REGION"
aws s3 cp "s3://$BUCKET/duckdb/duckdb-mvp.wasm" "s3://$BUCKET/duckdb/duckdb-mvp.wasm" \
  --content-type "application/wasm" --metadata-directive REPLACE --region "$CDK_DEFAULT_REGION"

# Invalidate cache
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" \
  --query 'Invalidation.Id' --output text --region "$CDK_DEFAULT_REGION"

echo ""
echo "✅ Deployed successfully!"
echo "   URL: $URL"
echo "   Bucket: $BUCKET"
echo "   Distribution: $DIST_ID"
echo ""
echo "   To tear down: cd infrastructure && cdk destroy"
