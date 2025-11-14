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

### 2. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
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
cd backend
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Then visit: http://localhost:3000

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

**"Port 5000 already in use"**
- Another process is using port 5000
- Kill it: `lsof -ti:5000 | xargs kill`

**Upload fails with "Cannot read image"**
- Verify file is valid JPEG
- Check file permissions
- Try re-saving image in different program
