# Quickstart Guide

Get up and running with the Hearing Test Tracker in 5 minutes.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Tesseract OCR installed on system

### Install Tesseract

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Verify Installation:**
```bash
tesseract --version
```

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd hearing-test-tracker
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Install Backend Dependencies

```bash
venv/bin/pip install -r backend/requirements.txt
```

**Note:** NumPy 1.x is required for opencv-python compatibility. If you encounter NumPy 2.x issues, downgrade:
```bash
venv/bin/pip install "numpy<2"
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## Running the Application

### Option 1: Use Run Script (Recommended)

```bash
python run.py
```

This starts both backend (port 5001) and frontend (port 3000), then opens your browser automatically.

### Option 2: Start Services Manually

**Terminal 1 - Backend:**
```bash
PYTHONPATH=$(pwd) venv/bin/python backend/app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then visit: **http://localhost:3000**

## Using the Application

### Dashboard View

The dashboard is your home page showing:
- **Stats Cards**: Total tests, latest test date, tests this year
- **Latest Test**: Quick view of your most recent test
- **Recent Tests Table**: Last 10 tests with confidence scores

### Upload a New Test

1. Click **"Upload Test"** in the navigation bar
2. Select a JPEG image of your audiogram
3. Click **"Process Audiogram"**
4. Wait for OCR to complete (~5-10 seconds)

**After Upload:**
- **High confidence (≥80%)**: Automatically redirected to test viewer
- **Low confidence (<80%)**: Redirected to review/edit page for manual correction

### View All Tests

1. Click **"All Tests"** in the navigation bar
2. Browse your complete test history in a sortable table
3. Click any row to view detailed test information

### View Test Details

From the test viewer page, you can:
- See the full audiogram chart with hearing loss zones
- View test metadata (date, location, device)
- Review measurement data for each ear
- **Edit** test data if needed
- **Delete** the test (with confirmation)

### Review and Edit Tests

On the review/edit page:
- **Left side**: Original audiogram image (click to zoom)
- **Right side**: Editable form with:
  - Test metadata (date, location, device, notes)
  - Measurement tables for left and right ear
- Click **"Accept & Save"** to confirm changes
- Click **"Cancel"** to discard changes

## Testing

Run backend tests:
```bash
cd backend
PYTHONPATH=.. pytest tests/ -v
```

Run integration test:
```bash
python test_integration.py
```

## Troubleshooting

**"Tesseract not found"**
- Install Tesseract (see Prerequisites)
- Verify installation: `tesseract --version`

**"Port 5001 already in use"**
- Another process is using port 5001
- Kill it: `lsof -ti:5001 | xargs kill`
- Note: Backend uses port 5001 (not 5000) to avoid macOS AirPlay conflict

**"NumPy version error" or "AttributeError: _ARRAY_API not found"**
- opencv-python requires NumPy 1.x, downgrade: `venv/bin/pip install "numpy<2"`

**"ModuleNotFoundError: No module named 'backend'"**
- Ensure PYTHONPATH is set when running backend manually
- Or use `python run.py` which handles this automatically

**Upload fails with "Cannot read image"**
- Verify file is valid JPEG
- Check file permissions
- Try re-saving image in different program
