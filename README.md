# Hearing Test Tracker

A desktop application for visualizing and analyzing audiogram data from hearing tests over time.

## Status

**Phase 1 Complete:** ✅ Core Infrastructure
- Database schema and utilities
- OCR pipeline (OpenCV + Tesseract)
- Flask REST API
- React + TypeScript frontend
- Basic upload workflow

**Phase 2 Complete:** ✅ Visualization Components
- Standard Audiogram Chart (inverted Y-axis, hearing loss zones)
- Frequency Trend Chart (time-series analysis)
- Calendar Heatmap (chronological view)
- Animated Timeline (morphing visualization)
- Multi-Test Comparison Grid (side-by-side analysis)

**Latest Updates:** 🎉 Enhanced OCR & Bulk Import
- **OCR Metadata Extraction**: Automatically extract date, time, device, and location from Jacoti audiograms
- **Bulk Upload**: Upload and process multiple audiograms at once from a folder
- **Improved Text Recognition**: Tesseract OCR integration for footer text extraction
- **Better Error Handling**: Individual file error handling in bulk uploads
- **Enhanced UI**: Tabbed upload interface with detailed results tables

**Next:** Phase 3 - Analysis & Reporting

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

### Guides
- [Quickstart Guide](docs/guides/quickstart.md) - Get started in 5 minutes
- [API Documentation](docs/api/endpoints.md) - Complete REST API reference

### Design & Planning
- [Design Document](docs/plans/2025-11-14-hearing-test-visualization-tool-design.md)
- [Implementation Plan](docs/plans/2025-11-14-phase1-core-infrastructure.md)

## Technology Stack

- **Backend:** Python 3.11+, Flask, SQLite, OpenCV, Tesseract
- **Frontend:** React 18, TypeScript, Vite, Mantine UI, TanStack Query, Recharts
- **Deployment:** Local desktop application (localhost)

