# Hearing Test Tracker

A desktop application for visualizing and analyzing audiogram data from hearing tests over time.

## Status

**Phase 1 Complete:** ✅ Core Infrastructure
- Database schema and utilities
- OCR pipeline (OpenCV + Tesseract)
- Flask REST API
- React + TypeScript frontend
- Basic upload workflow

**Next:** Phase 2 - Visualization components

## Quick Start

See [docs/guides/quickstart.md](docs/guides/quickstart.md) for detailed setup instructions.

```bash
# Install dependencies
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Run application
python run.py
```

## Documentation

- [Design Document](docs/plans/2025-11-14-hearing-test-visualization-tool-design.md)
- [Quickstart Guide](docs/guides/quickstart.md)
- [Implementation Plan](docs/plans/2025-11-14-phase1-core-infrastructure.md)

## Technology Stack

- **Backend:** Python 3.11+, Flask, SQLite, OpenCV, Tesseract
- **Frontend:** React 18, TypeScript, Vite, Mantine UI, TanStack Query
- **Deployment:** Local desktop application (localhost)

