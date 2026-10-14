# Architecture

> **⚠️ Educational use only.** This tool is built for education, demonstration, and
> learning purposes. It is **not intended for production use**. The architecture
> described below is deliberately simple (no auth, no CSP, no WAF, no monitoring)
> to keep the example readable, and would need hardening before any real-world
> deployment. Use at your own risk.

## Overview

The Parquet File Inspector is a **fully client-side** web application that inspects
Apache Parquet files using DuckDB compiled to WebAssembly. No server-side processing
occurs - the hosting infrastructure (S3 + CloudFront) only serves static assets.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  User's Browser                                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  index.html (Vanilla JS SPA)                          │  │
│  │                                                       │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐    │  │
│  │  │  Structure  │  │  Table View  │  │  SQL Query │    │  │
│  │  │  Explorer   │  │  (paginated) │  │  Console   │    │  │
│  │  └──────┬──────┘  └───────┬──────┘  └─────┬──────┘    │  │
│  │         │                 │               │           │  │
│  │         └─────────────────┼───────────────┘           │  │
│  │                           │                           │  │
│  │                    ┌──────▼──────┐                    │  │
│  │                    │  DuckDB     │                    │  │
│  │                    │  WASM       │◄── Web Worker      │  │
│  │                    │  (~35MB)    │                    │  │
│  │                    └──────┬──────┘                    │  │
│  │                           │                           │  │
│  │                    ┌──────▼──────┐                    │  │
│  │                    │  Parquet    │                    │  │
│  │                    │  File       │◄── ArrayBuffer     │  │
│  │                    │  (in memory)│    (from drag-drop │  │
│  │                    └─────────────┘     or fetch)      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS (static assets only)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  AWS Hosting                                                │
│                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────┐  │
│  │  CloudFront  │────▶│  S3 Bucket (private, OAC)        │  │
│  │  Distribution│     │                                  │  │
│  │  (HTTPS)     │     │  ├── index.html                  │  │
│  │              │     │  ├── duckdb/                     │  │
│  │  CF Function │     │  │   ├── duckdb-browser.mjs      │  │
│  │  (SPA route) │     │  │   ├── duckdb-eh.wasm          │  │
│  └──────────────┘     │  │   └── *.worker.js             │  │
│                       │  └── iot_sensors.parquet         │  │
│                       └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

1. User loads the page → CloudFront serves `index.html` + DuckDB WASM assets
2. DuckDB-WASM initializes in a Web Worker (loads ~35MB WASM binary)
3. User drops a Parquet file → read into an ArrayBuffer in the browser
4. ArrayBuffer is registered with DuckDB and copied for local hex inspection
5. DuckDB introspection functions extract metadata (schema, row groups, stats)
6. UI renders the metadata tree and enables the Table View / SQL tabs
7. SQL queries run entirely in-browser via DuckDB-WASM

**No data ever leaves the browser.** The Parquet file is processed locally in WebAssembly.

## Key Design Decisions

### Why DuckDB-WASM instead of a custom Thrift parser?

Parquet metadata is encoded in Apache Thrift compact protocol. Writing a correct
Thrift parser in JavaScript is error-prone (nested struct field ID tracking,
varint/zigzag encoding, type skipping). DuckDB already has a battle-tested Parquet
implementation and exposes the metadata via SQL functions - much more reliable.

### Why self-hosted WASM instead of CDN?

Browsers enforce strict same-origin policies for Web Workers. A Worker loaded from
`cdn.jsdelivr.net` cannot be instantiated by a page served from `d1234.cloudfront.net`.
Additionally, `.wasm` files require `Content-Type: application/wasm` for streaming
compilation - some CDNs serve them as `application/octet-stream`.

### Why a single HTML file?

The entire application is ~700 lines in a single `index.html`. This makes it:
- Easy to understand (one file, top-to-bottom)
- Easy to deploy (no build step, no bundler)
- Easy to modify (no framework overhead)

For a tool this size, a framework would add complexity without benefit.

## Security Model

| Concern | Mitigation |
|---------|-----------|
| Data exfiltration | The dropped Parquet file is never uploaded - it is read into an ArrayBuffer and parsed in-browser. No request carries file contents off the page. |
| S3 bucket exposure | BlockPublicAccess.BLOCK_ALL + CloudFront OAC |
| HTTPS | CloudFront enforces REDIRECT_TO_HTTPS; the bucket policy additionally denies non-TLS requests and TLS below 1.2 |
| XSS | Parquet-supplied values (column names, key-value metadata, statistics, file name, error messages) are HTML-escaped via `esc()` before every `innerHTML` assignment |
| Supply chain | DuckDB-WASM is self-hosted at a pinned version. **`apache-arrow` is loaded at runtime from `cdn.jsdelivr.net` via importmap and is not Subresource-Integrity pinned** - a compromise of that CDN would execute in the page. |

### Known gaps

Being a demo tool, the following are deliberately not addressed:

- No Content-Security-Policy header, so the Arrow CDN import is unconstrained.
- No SRI hash on the Arrow import (see Supply chain above).
- The loaded file name is interpolated into DuckDB SQL (`parquet_scan('${file.name}')`)
  without escaping. Impact is limited to the user's own in-browser DuckDB session.
- No authentication - the deployed site is public.

## Performance Characteristics

| Metric | Typical Value |
|--------|--------------|
| Initial page load | ~200KB (HTML + JS) |
| DuckDB WASM download | ~35MB (cached after first visit) |
| DuckDB initialization | 3-8 seconds (first load) |
| File parsing (50MB Parquet) | 2-5 seconds |
| SQL query (simple SELECT) | 50-200ms |
| Table pagination | <100ms |
