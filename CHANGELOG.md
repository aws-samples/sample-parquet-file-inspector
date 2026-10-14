# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-08

### Added
- Initial release of Parquet File Inspector
- Structure Explorer tab with file metadata, schema, row groups, column chunks
- Table View tab with paginated data display and type badges
- SQL Query tab powered by DuckDB-WASM
- Footer hex dump viewer
- Key-Value Metadata viewer with JSON prettification
- Drag-and-drop file loading (client-side only)
- Demo IoT sensor Parquet file (500K rows, 10 columns, 5 row groups)
- AWS CDK infrastructure (S3 + CloudFront OAC)
- One-command deploy script with WASM MIME type handling
- Self-hosted DuckDB-WASM for cross-origin compatibility
- Architecture and Parquet format documentation

### Technical Notes
- DuckDB-WASM v1.29.0 (self-hosted to avoid cross-origin Worker restrictions)
- Apache Arrow v17.0.0 (loaded via CDN import map)
- No backend - all processing happens in the browser via WebAssembly
- Estimated AWS cost: ~$1-2/month idle (CloudFront + S3 minimal request charges)
