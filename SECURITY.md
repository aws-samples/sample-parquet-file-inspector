# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it
responsibly. **Do not open a public GitLab issue for security vulnerabilities.**

### How to Report

Contact the maintainer directly:
- **Email:** pergamin@amazon.com
- **Subject:** `[SECURITY] parquet-file-inspector: <brief description>`

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment:** Within 48 hours
- **Assessment:** Within 1 week
- **Fix:** Dependent on severity

## Security Model

This application has a minimal attack surface:

| Vector | Risk | Mitigation |
|--------|------|-----------|
| File upload | Low | Files are processed client-side only; never uploaded to a server |
| XSS via file content | Low | All rendered values are text content, not innerHTML (except controlled templates) |
| DuckDB WASM | Low | Pinned version (v1.29.0), self-hosted; no dynamic loading from user-controlled sources |
| S3 bucket | None | BlockPublicAccess.BLOCK_ALL; CloudFront OAC only |
| Network exfiltration | None | No outbound requests after page load (except the optional demo file fetch from same origin) |

## Supported Versions

| Version | Supported |
|---------|-----------|
| main branch | ✅ Yes |

## Dependencies

This project has minimal dependencies:
- **Runtime:** DuckDB-WASM (MIT), Apache Arrow (Apache-2.0) — loaded in browser
- **Deploy-time:** AWS CDK (Apache-2.0) — not shipped to users

We recommend periodically updating DuckDB-WASM to pick up security fixes:
```bash
# Update the version in scripts/download-duckdb-wasm.sh and scripts/deploy.sh
# Then re-run the deploy
./scripts/deploy.sh
```
