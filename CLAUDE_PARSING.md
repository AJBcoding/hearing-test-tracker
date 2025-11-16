# Claude-Based Audiogram Parsing

This project uses Claude's multimodal capabilities to parse audiogram PDFs and images, replacing traditional OCR approaches.

## Benefits

### Traditional Approach (OCR)
- ❌ Requires manual hardcoding of PDF data (572 lines for House/UCLA tests)
- ❌ Uses OpenCV, Tesseract, and complex image processing pipelines
- ❌ Prone to errors in marker detection and coordinate transformation
- ❌ Requires maintenance when formats change

### Claude Approach
- ✅ **Automatic extraction** - No manual data entry needed
- ✅ **Native PDF/image reading** - Uses Claude's built-in capabilities
- ✅ **High accuracy** - Claude understands audiogram structure
- ✅ **Maintainable** - Simple API calls instead of complex pipelines
- ✅ **Format-agnostic** - Works with different audiogram layouts

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `anthropic>=0.39.0` - Claude API client

### 2. Get API Key

1. Visit https://console.anthropic.com/
2. Create an account or sign in
3. Generate an API key
4. Copy the key

### 3. Configure Environment

```bash
# Copy example env file
cp backend/.env.example backend/.env

# Edit backend/.env and add your API key
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Usage

### Import House Clinic / UCLA PDF Audiograms

```bash
# Using Claude parser (recommended)
python import_house_ucla_tests_claude.py

# Old approach (manual hardcoding - deprecated)
python import_house_ucla_tests.py
```

The Claude version will:
1. Read the PDF using Claude's native PDF capabilities
2. Extract ALL tests (including historical comparison data)
3. Parse structured audiogram data automatically
4. Import into database

### Import Jacoti Image Audiograms

```bash
# Using Claude parser (recommended)
python import_jacoti_tests_claude.py

# Old approach (OpenCV OCR - deprecated)
python import_jacoti_tests.py
```

The Claude version will:
1. Read JPEG images using Claude's vision API
2. Extract marker positions and threshold values
3. Parse footer metadata (date, time, device)
4. Calculate confidence scores
5. Import into database

## Parser API

### PDF Parsing

```python
from backend.ocr.claude_parser import parse_pdf_audiogram
from pathlib import Path

# Parse a PDF containing audiograms
pdf_path = Path('audiogram.pdf')
tests = parse_pdf_audiogram(pdf_path)

# Returns list of test dictionaries
for test in tests:
    print(f"Date: {test['test_date']}")
    print(f"Location: {test['location']}")
    print(f"Right ear: {test['right']}")  # {freq_hz: threshold_db}
    print(f"Left ear: {test['left']}")
```

### Image Parsing

```python
from backend.ocr.claude_parser import parse_image_audiogram
from pathlib import Path

# Parse a Jacoti audiogram image
image_path = Path('audiogram.jpeg')
result = parse_image_audiogram(image_path)

print(f"Date: {result['test_date']}")
print(f"Confidence: {result['confidence']}")
print(f"Right ear: {result['right_ear']}")
print(f"Left ear: {result['left_ear']}")
```

## Data Format

### PDF Extraction Output

```json
[
  {
    "test_date": "2024-01-12",
    "location": "House Clinic",
    "technician_name": "William H. Slattery MD",
    "device_name": "Insert Earphones",
    "notes": "Signed by: William H. Slattery MD",
    "right": {
      "250": 10,
      "500": 15,
      "1000": 10,
      "2000": 20,
      "4000": 30,
      "8000": 14
    },
    "left": {
      "250": 45,
      "500": 40,
      "1000": 15,
      "2000": 35,
      "4000": 50,
      "8000": 26
    },
    "right_bc": {
      "500": 60
    },
    "left_bc": {
      "2000": 70,
      "3000": 70
    }
  }
]
```

### Image Extraction Output

```json
{
  "test_date": "2024-12-07",
  "metadata": {
    "time": "12:24",
    "device": "Jacoti",
    "location": "Home",
    "raw_footer_text": "Made with Jacoti Hearing Center - 2024-12-07 12:24"
  },
  "right_ear": [
    {"frequency_hz": 125, "threshold_db": 25.0},
    {"frequency_hz": 250, "threshold_db": 15.0},
    {"frequency_hz": 500, "threshold_db": 10.0}
  ],
  "left_ear": [
    {"frequency_hz": 125, "threshold_db": 70.0},
    {"frequency_hz": 250, "threshold_db": 65.0},
    {"frequency_hz": 500, "threshold_db": 55.0}
  ],
  "confidence": 0.95
}
```

## Cost Considerations

Claude API usage is metered. Approximate costs:

- **PDF parsing**: ~$0.01-0.03 per page (depending on PDF size)
- **Image parsing**: ~$0.005-0.01 per image

For this project:
- House/UCLA PDF (10 pages): ~$0.10-0.30 one-time
- Jacoti images (~50 images): ~$0.25-0.50 one-time

Total one-time import cost: **< $1.00**

This is significantly cheaper than developer time for manual data entry or maintaining complex OCR pipelines.

## Migration Guide

### Replacing Old Import Scripts

1. **Test the new scripts first**:
   ```bash
   # Create a backup of your database
   cp backend/data/hearing_tests.db backend/data/hearing_tests.db.backup

   # Run new import
   python import_house_ucla_tests_claude.py
   ```

2. **Verify the data**:
   - Check that all tests were imported
   - Compare against old manual entries
   - Verify threshold values are accurate

3. **Switch permanently**:
   - Remove old import scripts (optional)
   - Update documentation to reference Claude versions
   - Enjoy automatic parsing! 🎉

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable not set"

Make sure you:
1. Created `backend/.env` file (copy from `backend/.env.example`)
2. Added your actual API key to the file
3. Restarted any running processes

### "JSON parsing error"

Claude's response might include markdown code blocks. The parser handles this automatically, but if you see errors:
- Check that your API key is valid
- Ensure the PDF/image is readable
- Try with a different file to isolate the issue

### Low confidence scores

For Jacoti images, confidence < 0.7 indicates:
- Image quality issues (blur, compression)
- Unusual marker positions
- Missing or unclear grid lines

Try:
- Using higher quality images
- Ensuring good lighting when capturing audiograms
- Checking that the image isn't cropped

## Future Enhancements

Possible improvements:
- [ ] Batch processing with rate limiting
- [ ] Caching to avoid re-parsing same files
- [ ] Support for additional audiogram formats
- [ ] Real-time parsing in web UI
- [ ] Comparison validation against old OCR results
