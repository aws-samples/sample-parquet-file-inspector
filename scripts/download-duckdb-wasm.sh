#!/bin/bash
# Downloads DuckDB-WASM binaries for self-hosting.
# Run this before deploying if the .wasm files are not present.

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DUCKDB_DIR="$SCRIPT_DIR/../src/frontend/duckdb"
VERSION="1.29.0"
CDN="https://cdn.jsdelivr.net/npm/@duckdb/duckdb-wasm@${VERSION}/dist"

echo "Downloading DuckDB-WASM v${VERSION}..."

curl -sL "$CDN/duckdb-eh.wasm" -o "$DUCKDB_DIR/duckdb-eh.wasm"
echo "  ✓ duckdb-eh.wasm ($(du -h "$DUCKDB_DIR/duckdb-eh.wasm" | cut -f1))"

curl -sL "$CDN/duckdb-mvp.wasm" -o "$DUCKDB_DIR/duckdb-mvp.wasm"
echo "  ✓ duckdb-mvp.wasm ($(du -h "$DUCKDB_DIR/duckdb-mvp.wasm" | cut -f1))"

echo "Done. WASM binaries are in: $DUCKDB_DIR"
