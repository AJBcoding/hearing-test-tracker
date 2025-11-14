# Hearing Test Visualization Tool - Design Document

**Date:** 2025-11-14
**Project:** Hearing Test Analysis & Visualization
**Status:** Design Complete - Ready for Implementation

---

## Executive Summary

This tool visualizes and analyzes audiogram data from hearing tests over time. Users can upload historical test images, track changes, identify patterns, and generate professional reports. The system runs locally as a desktop application, processes images with OCR, stores data in a database, and presents multiple interactive visualizations.

**Key Capabilities:**
- Import 22 historical audiogram images via automated OCR
- Track hearing thresholds across 9 frequencies (64Hz - 16kHz) per ear
- Visualize data in 5 modes: standard audiogram, time-series, heatmap, animation, comparison grid
- Analyze trends with statistical calculations and seasonal pattern detection
- Generate PDF reports for clinical sharing

**Technology Stack:**
- Backend: Python (Flask) + PostgreSQL/SQLite
- Frontend: React + TypeScript + Mantine UI + Recharts
- OCR: OpenCV + Tesseract
- Deployment: Local desktop application (localhost)

---

## System Architecture

### Component Overview

The application comprises three layers, all running on the local machine:

**1. Python Backend (Flask API)**
- Port: `localhost:5000`
- Handles OCR processing (OpenCV + Tesseract)
- Manages database operations
- Calculates statistical analyses
- Generates PDF reports

**Key API Endpoints:**
```
POST /api/tests/upload              # Upload audiogram image for OCR
GET  /api/tests                     # List all tests with metadata
GET  /api/tests/{id}                # Retrieve specific test details
GET  /api/analysis/trends           # Calculate statistical trends
GET  /api/analysis/compare          # Compare selected tests
POST /api/tests/manual              # Manual data entry
GET  /api/export/pdf/{test_id}      # Generate PDF report
```

**2. Database Layer**
- Primary: SQLite (single-file, zero configuration)
- Migration path: PostgreSQL (if multi-user needed)
- Stores: test metadata, measurements, OCR results, comparisons

**3. React Frontend**
- Development: `localhost:3000` (Vite dev server)
- Production: Static files served by Flask
- Tech: TypeScript + Mantine (UI components) + Recharts (visualization)
- State: TanStack React Query for server state caching

**Key Views:**
- Dashboard - Recent tests and quick statistics
- Audiogram Viewer - Multiple visualization modes (tabs)
- Test Comparison - Side-by-side analysis
- Analysis Reports - Trends and patterns
- Upload & Import - Image processing interface

**Deployment:**
- Single command starts Flask server: `python run.py`
- Browser auto-opens to localhost:5000
- All data remains local (privacy-first)
- Future: Package as standalone executable (PyInstaller)

---

## Database Schema

Following Python419 conventions: UUID primary keys, `id_TableName` foreign keys, lowercase naming.

### Core Tables

**`hearing_test`** - Test records
```sql
CREATE TABLE hearing_test (
    id TEXT PRIMARY KEY,                    -- UUID
    test_date TIMESTAMP NOT NULL,           -- Test date
    test_time TIME,                         -- Time of day
    source_type TEXT NOT NULL,              -- 'audiologist' | 'home'
    location TEXT,                          -- 'House Ear Clinic', 'Jacoti Home'
    device_name TEXT,                       -- 'Jacoti', 'Interacoustics'
    technician_name TEXT,                   -- For clinic visits
    notes TEXT,                             -- Clinical observations
    image_path TEXT,                        -- Path to original JPEG
    ocr_confidence FLOAT,                   -- 0.0-1.0 quality score
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_test_date ON hearing_test(test_date DESC);
```

**`audiogram_measurement`** - Frequency/threshold data points
```sql
CREATE TABLE audiogram_measurement (
    id TEXT PRIMARY KEY,                    -- UUID
    id_hearing_test TEXT NOT NULL,          -- FK to hearing_test
    ear TEXT NOT NULL,                      -- 'left' | 'right'
    frequency_hz INTEGER NOT NULL,          -- 64, 125, 250, 500, 1k, 2k, 4k, 8k, 16k
    threshold_db FLOAT NOT NULL,            -- Hearing loss in dB HL (0-120)
    is_no_response BOOLEAN DEFAULT FALSE,   -- True if threshold > 120 dB
    measurement_type TEXT,                  -- 'air_conduction' | 'bone_conduction'
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(id_hearing_test, ear, frequency_hz, measurement_type),
    FOREIGN KEY(id_hearing_test) REFERENCES hearing_test(id)
);

CREATE INDEX idx_measurement_lookup
    ON audiogram_measurement(id_hearing_test, ear, frequency_hz);
```

**`test_comparison`** - Saved comparisons
```sql
CREATE TABLE test_comparison (
    id TEXT PRIMARY KEY,
    comparison_name TEXT,                   -- User-defined label
    test_ids TEXT[],                        -- Array of hearing_test IDs
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Data Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Primary Keys | UUID strings | `'a3f2c1b5-...'` |
| Foreign Keys | `id_TableName` | `id_hearing_test` |
| Table Names | Lowercase singular | `hearing_test` |
| Column Names | Lowercase with underscores | `frequency_hz` |
| Booleans | `is_` prefix | `is_no_response` |
| Timestamps | `created_at`, `modified_at` | Auto-update via trigger |

---

## OCR Pipeline (OpenCV + Tesseract)

The OCR pipeline extracts audiogram data from JPEG images in five stages.

### Stage 1: Image Preprocessing

```python
def preprocess_image(image_path):
    """
    Prepare image for OCR and marker detection.

    Steps:
    1. Load image with OpenCV (2190x1275 pixels typical)
    2. Convert to grayscale
    3. Apply adaptive thresholding for contrast
    4. Deskew if rotated (detect lines, correct angle)
    5. Segment graph region from text regions

    Returns: preprocessed image, graph bounds
    """
```

### Stage 2: Text Extraction (Tesseract)

```python
def extract_metadata(preprocessed_image):
    """
    Extract text metadata from image.

    Targets:
    - Test date/time (top of image)
    - Clinic name ("Jacoti Hearing Center")
    - Patient info (if present)
    - Axis labels (frequencies, dB scale)

    Returns: dict with metadata fields
    """
```

### Stage 3: Graph Region Analysis (OpenCV)

```python
def detect_audiogram_markers(graph_region):
    """
    Locate data point markers using color detection.

    Process:
    1. Isolate red channel → find red circles (right ear)
    2. Isolate blue channel → find blue X markers (left ear)
    3. Apply contour detection to locate each marker
    4. Calculate centroid of each marker → pixel coordinates (x, y)

    Returns: list of marker positions by ear
    """
```

### Stage 4: Coordinate Transformation

```python
def convert_pixels_to_audiogram_values(markers, graph_bounds):
    """
    Map pixel positions to dB/Hz values.

    Process:
    1. Detect axis boundaries (find graph edges)
    2. Map x-axis pixels → frequency values (64-16000 Hz, log scale)
    3. Map y-axis pixels → dB values (0-120 dB, linear scale, inverted)
    4. For each marker: (pixel_x, pixel_y) → (frequency_hz, threshold_db)
    5. Validate frequencies match standard audiometric set

    Returns: list of (ear, frequency_hz, threshold_db) tuples
    """
```

### Stage 5: Quality Validation

```python
def calculate_ocr_confidence(extracted_data):
    """
    Score OCR quality for human review decision.

    Checks:
    - Marker count: 9 per ear expected
    - Frequency validation: match audiometric standards
    - Outlier detection: dB values in 0-120 range
    - Metadata completeness: date extracted

    Returns: confidence score (0.0 - 1.0)
    - < 0.8: Flag for human review
    - >= 0.8: Auto-save to database
    """
```

### Format Adapters

Pluggable parser architecture supports multiple clinic formats:

```
parsers/
├── jacoti_parser.py          # Primary format (2190x1275, red/blue markers)
├── house_ear_parser.py       # Future: House Ear Clinic format
└── parser_registry.py        # Auto-detect format, route to correct parser
```

**Detection Strategy:**
1. Check image dimensions
2. Scan for clinic name in header text
3. Analyze marker colors/shapes
4. Route to appropriate parser

---

## Visualization Components (React + Recharts)

The frontend provides five visualization modes, accessible via Mantine Tabs.

### Mode 1: Standard Audiogram View

**Component:** `AudiogramChart.tsx`

Displays traditional audiogram graph with interactive overlays.

**Chart Configuration:**
- Library: Recharts LineChart with dual Y-axes
- X-axis: Frequencies (64Hz - 16kHz), logarithmic scale
- Y-axis: Hearing loss (0-120 dB HL), **inverted** (0 at top, 120 at bottom)
- Series:
  - Right ear: Red line, circle markers
  - Left ear: Blue line, X markers

**Interactive Features:**
- Test selector dropdown (switch between dates)
- Overlay mode toggle (show multiple tests, semi-transparent)
- Hover tooltips (exact dB value at each frequency)
- Shaded zones:
  - Normal: 0-25 dB (light green)
  - Mild loss: 26-40 dB (yellow)
  - Moderate: 41-55 dB (orange)
  - Severe: 56-70 dB (red)
  - Profound: 71+ dB (dark red)

### Mode 2: Time-Series Progression

**Component:** `FrequencyTrendChart.tsx`

Tracks single frequency over time.

**Chart Configuration:**
- X-axis: Test dates (chronological)
- Y-axis: Hearing threshold (dB HL)
- Dual lines: Left ear (blue), Right ear (red)

**Features:**
- Frequency selector buttons: [125Hz] [500Hz] [1kHz] [2kHz] [4kHz] [8kHz]
- Linear regression trend line overlay
- Annotations distinguish clinic vs. home tests (icon markers)
- Zoom controls for date range

### Mode 3: Heatmap Calendar View

**Component:** `TestCalendarHeatmap.tsx`

Shows testing frequency and overall health at a glance.

**Display:**
- Calendar grid layout (months across top, years down side)
- Each test date = colored cell
- Color scale: Green (good) → Yellow → Orange → Red (severe)
- Color based on average hearing loss across all frequencies
- Click cell to navigate to that test's audiogram

### Mode 4: Animated Timeline

**Component:** `AudiogramAnimation.tsx`

Morphs audiogram curves through time.

**Controls:**
- Play/pause button
- Speed slider (0.5x - 5x)
- Scrubber timeline (drag to specific date)
- Auto-loop toggle
- Current date display (updates during playback)

**Animation:**
- Smooth interpolation between test dates
- Synchronized left/right ear curves
- Highlights regions of significant change during playback

### Mode 5: Multi-Test Comparison Grid

**Component:** `ComparisonGrid.tsx`

Side-by-side audiogram display.

**Layout:**
- Select 2-4 tests via checkbox list
- Grid arrangement (2x2 max)
- Synchronized axes for easy comparison
- Difference overlay mode (color-coded regions where hearing changed >10dB)

### Navigation & State Management

**Tabs Component (Mantine):**
```tsx
<Tabs defaultValue="audiogram">
  <Tabs.List>
    <Tabs.Tab value="audiogram">Audiogram</Tabs.Tab>
    <Tabs.Tab value="trends">Trends</Tabs.Tab>
    <Tabs.Tab value="calendar">Calendar</Tabs.Tab>
    <Tabs.Tab value="animation">Animation</Tabs.Tab>
    <Tabs.Tab value="compare">Compare</Tabs.Tab>
  </Tabs.List>
  {/* Tab panels */}
</Tabs>
```

**Shared State:**
- Selected test(s): React Context
- Date range filters: URL query params
- Data caching: TanStack React Query (5-minute stale time)

---

## Analysis & Reporting

The backend provides statistical analysis and professional reporting capabilities.

### Statistical Analysis Features

**1. Change Detection**

```python
# Backend: analysis/change_detector.py

def compare_tests(test_id_1: str, test_id_2: str) -> dict:
    """
    Compare two tests and identify significant changes.

    Returns:
        frequency_changes: Dict[frequency_hz -> delta_db]
        significant_changes: List of frequencies where |delta| > 10dB
        overall_trend: 'improving' | 'declining' | 'stable'
        ear_asymmetry: Difference between left/right progression rates
    """
```

**2. Trend Analysis**

```python
# Backend: analysis/trend_analyzer.py

def calculate_trends(test_ids: List[str], ear: str, frequency_hz: int) -> dict:
    """
    Calculate linear regression over time for specific frequency.

    Returns:
        slope_db_per_year: Rate of hearing change (negative = improving)
        r_squared: Trend confidence (0-1)
        prediction_1_year: Projected threshold in 12 months
        is_significant: Boolean (p-value < 0.05)
    """
```

**3. Seasonal Pattern Detection**

```python
# Backend: analysis/pattern_detector.py

def detect_seasonal_patterns(test_ids: List[str]) -> dict:
    """
    Group tests by season/month, identify variations.

    Returns:
        monthly_averages: Dict[month -> avg_threshold_db]
        seasonal_variation: Dict[season -> avg_threshold_db]
        peak_loss_period: Month with worst hearing
        best_period: Month with best hearing
        is_statistically_significant: Boolean (requires 12+ months data)
    """
```

**4. Rate of Change Calculator**

```python
# Backend: analysis/rate_calculator.py

def calculate_rate_of_change(test_ids: List[str],
                            time_window: str = '6_months') -> dict:
    """
    Calculate rolling average change rate.

    Returns per frequency:
        db_change_per_month: Average monthly deterioration/improvement
        acceleration: Is rate increasing or decreasing?
        projected_mild_loss_date: When threshold crosses 25dB (if trending)
    """
```

### Professional Reporting

**Report Types:**

**A) Summary Report** (PDF Export)
- Patient header (name, date range)
- Latest audiogram visualization
- Statistics table (average thresholds per frequency)
- Trend summary (improving/stable/declining per frequency)
- Notes section for audiologist annotations
- Generated via `reportlab` library

**B) Comparison Report**
- Side-by-side audiograms (selected tests)
- Difference table (dB changes per frequency)
- Highlighted significant changes (>10dB threshold)
- Recommendations flag if rapid decline detected (>15dB in 6 months)

**C) Longitudinal Report**
- Timeline of all tests (date, location, overall status)
- Trend charts for critical frequencies (500Hz, 1kHz, 2kHz, 4kHz)
- Seasonal analysis (if >12 months data available)
- Testing frequency analysis (gaps between tests flagged)

**Export Formats:**
- PDF (professional sharing with audiologist)
- CSV (raw data export for external analysis)
- JSON (backup/migration format)

**Frontend UI:**
- Mantine `Card` components for analysis sections
- `Badge` components highlight significant findings
- `Alert` component for warnings (rapid decline detected)
- Export buttons in page header

---

## User Workflows & Error Handling

### Initial Setup & Historical Migration

**First Launch:**

```
1. User runs: python run.py
2. System detects empty database
3. Welcome screen renders with two options:
   - "Import Historical Tests" (primary action)
   - "Start Fresh" (skip import)
```

**Import Workflow:**

```
1. User clicks "Import Historical Tests"
2. File picker opens (defaults to "Hearing test Archive")
3. System scans folder for .jpeg files
4. Preview list displays:
   - Filename
   - Detected date (from OCR preview)
   - Estimated confidence score
   - Checkbox (user can deselect before import)
5. User clicks "Import Selected"
6. Batch processing begins:
   - Progress bar: "Processing 18 of 22 tests..."
   - Each test: extract → validate → save or flag
7. Import summary displays:
   - "Successfully imported: 20 tests"
   - "Needs review: 2 tests (low confidence)"
   - Button: "Review Flagged Tests"
```

**Manual Review Flow:**

```
1. Shows original image side-by-side with extracted data table
2. User can:
   - Edit date/metadata fields directly
   - Click on image to manually place missing markers
   - Adjust frequency/dB values in table
   - Mark as "Correct" or "Delete"
3. Save corrections → updates database with manual flag
```

### Adding New Tests

**Scenario A: Upload Audiogram Image**

```
1. Click "Upload Test" button
2. File picker opens
3. Select JPEG image
4. OCR processing (loading spinner with progress: "Extracting data...")
5. Preview screen renders:
   - Extracted audiogram chart (live preview)
   - Editable metadata form (date, location, device, notes)
   - Confidence score badge (color-coded)
6. User reviews/edits → clicks "Save"
7. Success notification → redirects to latest test view
```

**Scenario B: Manual Entry**

```
1. Click "Enter Test Manually" button
2. Form appears:
   - Date picker (calendar widget)
   - Location dropdown (populated from previous entries)
   - Device dropdown
   - Notes textarea
3. Interactive audiogram grid:
   - Tabs: [Left Ear] [Right Ear]
   - Input fields for each frequency (64Hz-16kHz)
   - Alternative: Click on blank audiogram to place points visually
4. Validation on save:
   - Check all 9 frequencies present per ear
   - Verify dB values in 0-120 range
5. Save → database insert → redirect to test view
```

### Daily Usage Patterns

**Pattern 1: Quick Check** (Most Common)

```
1. Launch app (browser opens to localhost:5000)
2. Dashboard loads with:
   - Latest test card (mini audiogram preview)
   - Recent changes summary: "No significant changes in last 30 days"
   - Next recommended test date
3. User scans summary, closes app (or clicks test for details)
```

**Pattern 2: Compare Two Tests**

```
1. Navigate to "Compare" tab
2. Select two tests from dropdown date pickers
3. Comparison grid renders automatically
4. Review difference table in panel below
5. Optional: Click "Export PDF Report"
```

**Pattern 3: Analyze Trends**

```
1. Navigate to "Trends" tab
2. Select frequency of interest (click button: 4kHz)
3. Time-series chart renders with trend line
4. Toggle "Group by Season" checkbox
5. Review statistics panel (slope, projection)
```

### Error Handling

**OCR Failures:**

| Scenario | Response |
|----------|----------|
| Low confidence (< 0.8) | Flag for manual review, show warning badge, do not auto-save |
| No markers detected | Error modal: "Unable to detect audiogram markers. Try manual entry." |
| Ambiguous date | Prompt with best guess: "Detected date: 2024-12-15. Correct?" |
| Corrupted image | "Cannot read image file. Verify file is valid JPEG." |

**Data Validation:**

| Scenario | Response |
|----------|----------|
| Duplicate test (same date/time/location) | Confirmation dialog: "Test from this date exists. Replace or keep both?" |
| Out-of-range dB | Error: "Threshold 150dB invalid (max 120). Please verify." |
| Missing frequencies | Warning badge, allow partial save with note |

**System Errors:**

| Scenario | Response |
|----------|----------|
| Database connection lost | Error modal with "Retry" button |
| API timeout | Toast notification: "Request timed out. Retrying..." (exponential backoff) |
| Image file too large | "Image exceeds 10MB limit. Compress and retry." |

### File Management

**Storage Paths:**
- Original images: `data/audiograms/YYYY-MM-DD_HHMMSS.jpeg`
- Database: `data/hearing_tests.db` (SQLite)
- Backups: `backups/YYYY-MM-DD.json` (weekly auto-export)
- Exports: `exports/reports/YYYY-MM-DD_report.pdf`

**Backup Strategy:**
- Auto-export JSON every 7 days
- Backup includes: all test records, measurements, metadata
- Restore function: Import JSON to rebuild database

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

**Goals:** Database, API skeleton, basic OCR

**Tasks:**
1. Set up project structure (backend/, frontend/, docs/)
2. Create database schema with migrations
3. Build Flask API with basic endpoints
4. Implement simple Jacoti OCR parser (Stage 1-4)
5. Create React app with Mantine setup
6. Basic file upload UI

**Deliverable:** Upload a Jacoti JPEG, extract data, save to database, display in simple table

### Phase 2: Visualization (Week 3-4)

**Goals:** All 5 visualization modes

**Tasks:**
1. Implement AudiogramChart (Mode 1)
2. Add FrequencyTrendChart (Mode 2)
3. Build TestCalendarHeatmap (Mode 3)
4. Create AudiogramAnimation (Mode 4)
5. Implement ComparisonGrid (Mode 5)
6. Add Tabs navigation

**Deliverable:** View historical data in all 5 modes

### Phase 3: Analysis & Reporting (Week 5)

**Goals:** Statistical analysis, PDF generation

**Tasks:**
1. Implement change_detector.py
2. Build trend_analyzer.py with linear regression
3. Add pattern_detector.py for seasonal analysis
4. Create rate_calculator.py
5. Build PDF report generator (reportlab)
6. Add export functionality (CSV, JSON)

**Deliverable:** Generate professional PDF reports

### Phase 4: Historical Migration & Polish (Week 6)

**Goals:** Import 22 historical tests, UX refinement

**Tasks:**
1. Batch OCR processor with progress tracking
2. Manual review interface for low-confidence extractions
3. Error handling improvements
4. Performance optimization (caching, lazy loading)
5. User testing with real data
6. Documentation (user guide)

**Deliverable:** All 22 historical tests imported and validated

### Phase 5: Packaging & Deployment (Week 7)

**Goals:** Standalone application

**Tasks:**
1. Production build configuration
2. Flask serves React static files
3. Package with PyInstaller
4. Create installer for macOS
5. User manual and troubleshooting guide
6. Final testing

**Deliverable:** Double-click app that runs without Python installation

---

## Technology Decisions & Rationale

### Why Flask + React (Not Electron, PyQt, or Streamlit)?

**Flask + React:**
- ✅ Leverage Python419 tech stack (familiar patterns)
- ✅ Best-in-class charting (Recharts handles complex animations)
- ✅ Python ideal for OCR/image processing
- ✅ Easy development (hot reload, TypeScript safety)
- ✅ Simple deployment (run Python script, browser opens)
- ✅ Future packaging option (PyInstaller bundles everything)

**Why NOT alternatives:**
- ❌ **Streamlit:** Too limiting for complex multi-view animations
- ❌ **PyQt/PySide:** Steeper learning curve, inferior charting libraries
- ❌ **Electron:** Unnecessary complexity/bloat for local-only app
- ❌ **Tauri:** Rust backend doesn't help with Python OCR pipeline

### Why SQLite (Not PostgreSQL initially)?

**SQLite advantages for this use case:**
- ✅ Zero configuration (no server setup)
- ✅ Single file (easy backup, portable)
- ✅ Sufficient for single-user desktop app
- ✅ Fast for <1000 records (decades of tests)

**Migration path to PostgreSQL:**
- Later add multi-user features (family sharing)
- Cloud backup/sync capabilities
- Large dataset (>10,000 tests)

### Why OpenCV + Tesseract (Not ML)?

**OpenCV approach:**
- ✅ Fast development (days, not weeks)
- ✅ Reliable for consistent formats (Jacoti layout stable)
- ✅ Lightweight dependencies
- ✅ Interpretable results (debug failures easily)
- ✅ No training data required

**ML approach would require:**
- ❌ Collect 100s of labeled examples
- ❌ Weeks to train and tune model
- ❌ GPU for reasonable performance
- ❌ Overkill for 22 images from 1-2 sources

---

## Success Criteria

This design succeeds if the implemented system:

1. **Imports all 22 historical tests** with >90% accuracy (OCR confidence >0.8)
2. **Renders all 5 visualization modes** smoothly (<100ms to switch views)
3. **Generates accurate reports** (statistical calculations match manual verification)
4. **Runs on single command** (no multi-step setup process)
5. **Provides clear error messages** when OCR fails or data invalid
6. **Exports professional PDFs** suitable for sharing with audiologist

---

## Future Enhancements

Potential additions beyond initial scope:

1. **Multi-user support** (family accounts, separate databases)
2. **Cloud backup** (optional encrypted sync)
3. **Mobile app** (view tests on phone, limited functionality)
4. **Additional parsers** (support 10+ clinic formats)
5. **ML-assisted OCR** (if processing >1000 varied images)
6. **Correlation analysis** (link hearing changes to medications, allergies)
7. **Reminder system** (notify when next test due)
8. **Audiologist portal** (share read-only link to test history)

---

## Conclusion

This design creates a practical, privacy-focused tool for tracking hearing health over time. By leveraging proven technologies (Python, React, PostgreSQL) and following established patterns from the Python419 project, development risk remains low. The OCR pipeline handles the unique challenge of extracting data from audiogram images, while the multi-modal visualization approach provides comprehensive views of the data.

The phased implementation roadmap delivers value incrementally: core functionality first, then analysis features, followed by historical migration and polish. This ensures the system remains usable throughout development while building toward the complete vision.

Next step: Create detailed implementation plan with specific tasks, file paths, and code examples for each phase.
