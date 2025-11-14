# Quickstart Guide

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

## Installation

### 1. Clone Repository

```bash
cd /Users/anthonybyrnes/PycharmProjects/hearing-test-tracker
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

### 3. Install Backend Dependencies

```bash
venv/bin/pip install -r backend/requirements.txt
```

Note: NumPy 1.x is required for opencv-python compatibility. If you encounter NumPy 2.x issues, downgrade:
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

This starts both backend and frontend, then opens your browser automatically.

### Option 2: Start Services Manually

**Terminal 1 - Backend:**
```bash
PYTHONPATH=/Users/anthonybyrnes/PycharmProjects/hearing-test-tracker venv/bin/python backend/app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then visit: http://localhost:3000 (or the port shown by Vite if 3000 is in use)

## Using the Application

1. Click "Upload Audiogram" button
2. Select a JPEG image of your audiogram
3. Click "Process Audiogram"
4. Wait for OCR to complete (~5-10 seconds)
5. Review extracted data in table below
6. If confidence < 80%, manual review recommended

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
