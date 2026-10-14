# Contributing to Parquet File Inspector

Thank you for your interest in contributing! This document provides guidelines
for contributing to this project.

## How to Contribute

### Reporting Issues

- Use GitLab Issues to report bugs or request features
- Include browser version, OS, and steps to reproduce for bug reports
- Attach a sample Parquet file (or describe its schema) if the issue is file-specific

### Submitting Changes

1. Fork the repository
2. Create a feature branch from `main` (`git checkout -b feature/my-change`)
3. Make your changes, following the coding guidelines below
4. Test locally (`python3 -m http.server 8080` in `src/frontend/`)
5. Commit with a descriptive message (see commit format below)
6. Push to your fork and open a Merge Request

### Commit Message Format

```
type(scope): short description

Longer description if needed.
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
- `feat(ui): add column sorting in table view`
- `fix(duckdb): handle files with no key-value metadata`
- `docs: add screenshot of row group view`

## Coding Guidelines

### Frontend (src/frontend/)

- **No build step.** The app is a single HTML file - keep it that way.
- **No frameworks.** Vanilla JS, CSS custom properties for theming.
- **Comments.** Add JSDoc-style comments for functions. Explain *why*, not *what*.
- **Accessibility.** New UI elements should have ARIA labels and keyboard support.
- **Error handling.** Always catch and display errors to the user - never fail silently.

### Infrastructure (infrastructure/)

- **CDK only.** No raw CloudFormation templates.
- **Comments.** Every construct should have a comment explaining its purpose.
- **Security.** Never open S3 to public. Never add Lambda without least-privilege IAM.

### Scripts (scripts/)

- **Portable.** Scripts should work on macOS and Linux.
- **Idempotent.** Running a script twice should produce the same result.
- **Verbose.** Print what you're doing at each step.

## Development Setup

```bash
# Clone
git clone git@ssh.gitlab.aws.dev:pergamin/parquet-file-inspector.git
cd parquet-file-inspector

# Download DuckDB WASM binaries
./scripts/download-duckdb-wasm.sh

# Generate sample data (optional - needs pyarrow)
pip3 install pyarrow numpy
python3 scripts/generate_sample_data.py

# Serve locally
cd src/frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

## Testing

### Manual Testing Checklist

Before submitting a MR, verify:

- [ ] Demo file loads successfully via "Load Demo File" button
- [ ] Drag-and-drop works with a real Parquet file
- [ ] All three tabs render correctly (Structure, Table View, SQL Query)
- [ ] Schema shows column names and types (not "GROUP" for everything)
- [ ] Key-Value Metadata shows decoded strings (not raw bytes)
- [ ] Hex Dump renders footer bytes
- [ ] SQL queries execute and return results
- [ ] Page works in Chrome, Firefox, and Safari
- [ ] No console errors in the browser developer tools

### CDK Testing

```bash
cd infrastructure
npm install
npx cdk synth  # Should produce CloudFormation without errors
```

## Code of Conduct

This project follows the [Amazon Open Source Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT-0 License.
