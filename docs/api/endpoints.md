# API Documentation

REST API endpoints for the Hearing Test Tracker application.

**Base URL:** `http://localhost:5001/api`

---

## Tests

### Upload Single Audiogram

Upload and process a single audiogram image.

**Endpoint:** `POST /tests/upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `file`: JPEG/PNG image file

**Response:** `200 OK`
```json
{
  "test_id": "uuid-string",
  "confidence": 0.85,
  "needs_review": false,
  "left_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 25.0
    },
    // ... more measurements
  ],
  "right_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 20.0
    },
    // ... more measurements
  ]
}
```

**Error Response:** `500 Internal Server Error`
```json
{
  "error": "Error message describing what went wrong"
}
```

---

### Bulk Upload Audiograms (NEW!)

Upload and process multiple audiogram images at once.

**Endpoint:** `POST /tests/bulk-upload`

**Request:**
- Content-Type: `multipart/form-data`
- Body:
  - `files[]`: Multiple JPEG/PNG image files (array)

**Example using curl:**
```bash
curl -X POST http://localhost:5001/api/tests/bulk-upload \
  -F "files[]=@audiogram1.jpeg" \
  -F "files[]=@audiogram2.jpeg" \
  -F "files[]=@audiogram3.jpeg"
```

**Response:** `200 OK`
```json
{
  "total": 3,
  "successful": 2,
  "failed": 1,
  "results": [
    {
      "filename": "audiogram1.jpeg",
      "status": "success",
      "test_id": "uuid-1",
      "confidence": 0.85,
      "needs_review": false
    },
    {
      "filename": "audiogram2.jpeg",
      "status": "success",
      "test_id": "uuid-2",
      "confidence": 0.65,
      "needs_review": true
    },
    {
      "filename": "audiogram3.jpeg",
      "status": "error",
      "error": "Cannot read image: corrupted file"
    }
  ]
}
```

**Features:**
- Processes files independently (one failure doesn't affect others)
- Returns detailed results for each file
- Failed uploads are automatically cleaned up
- Supports any number of files (limited by server memory)

**Error Response:** `400 Bad Request`
```json
{
  "error": "No files provided"
}
```

---

### List All Tests

Get a list of all hearing tests.

**Endpoint:** `GET /tests`

**Response:** `200 OK`
```json
[
  {
    "id": "uuid-string",
    "test_date": "2024-12-17",
    "source_type": "home",
    "location": "Jacoti Hearing Center",
    "confidence": 0.85
  },
  // ... more tests
]
```

**Query Parameters:** None

**Sorting:** Results are sorted by `test_date` DESC (newest first)

---

### Get Test Details

Get detailed information about a specific test.

**Endpoint:** `GET /tests/{test_id}`

**Path Parameters:**
- `test_id`: UUID of the test

**Response:** `200 OK`
```json
{
  "id": "uuid-string",
  "test_date": "2024-12-17",
  "source_type": "home",
  "location": "Jacoti Hearing Center",
  "left_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 25.0
    },
    // ... more measurements
  ],
  "right_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 20.0
    },
    // ... more measurements
  ],
  "metadata": {
    "device": "Jacoti Hearing Center",
    "technician": "",
    "notes": "",
    "confidence": 0.85,
    "image_path": "/path/to/image.jpeg"
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "error": "Test not found"
}
```

---

### Update Test

Update test data after manual review or correction.

**Endpoint:** `PUT /tests/{test_id}`

**Path Parameters:**
- `test_id`: UUID of the test

**Request:**
- Content-Type: `application/json`
```json
{
  "test_date": "2024-12-17",
  "location": "Jacoti Hearing Center",
  "device_name": "Jacoti",
  "notes": "Optional notes about the test",
  "left_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 25.0
    }
    // ... more measurements
  ],
  "right_ear": [
    {
      "frequency_hz": 250,
      "threshold_db": 20.0
    }
    // ... more measurements
  ]
}
```

**Response:** `200 OK`
- Returns the updated test object (same format as GET /tests/{test_id})

**Notes:**
- Measurements are automatically deduplicated by frequency (median value used)
- All existing measurements are replaced with the new data

**Error Response:** `404 Not Found`
```json
{
  "error": "Test not found"
}
```

---

### Delete Test

Delete a test and its measurements.

**Endpoint:** `DELETE /tests/{test_id}`

**Path Parameters:**
- `test_id`: UUID of the test

**Response:** `200 OK`
```json
{
  "success": true
}
```

**Notes:**
- Also deletes the associated audiogram image file
- Measurements are cascade-deleted automatically

**Error Response:** `404 Not Found`
```json
{
  "error": "Test not found"
}
```

---

## OCR Details

### Metadata Extraction (NEW!)

The OCR system now automatically extracts metadata from Jacoti audiogram images:

**Extracted Fields:**
- `test_date`: Date in YYYY-MM-DD format (e.g., "2024-12-17")
- `time`: Time in HH:MM format (e.g., "12:24")
- `device`: Device/software name (e.g., "Jacoti Hearing Center")
- `location`: Location/facility name (e.g., "Jacoti Hearing Center")

**Footer Format Supported:**
```
Made with Jacoti Hearing Center - 2024-12-17 12:24
```

**How It Works:**
1. **Image Preprocessing:**
   - Extract footer region (bottom 10% of image)
   - Convert to grayscale
   - Apply adaptive thresholding for better text contrast

2. **Text Extraction:**
   - Tesseract OCR with custom config (`--oem 3 --psm 6`)
   - Extract raw text from footer

3. **Parsing:**
   - Regex pattern matching for "Made with [device] - [date] [time]"
   - Fallback to date-only extraction if full pattern fails
   - Date format normalization (slashes converted to dashes)

4. **Marker Detection:**
   - Red circles: Right ear measurements
   - Blue X marks: Left ear measurements
   - Color-based HSV filtering with morphological operations

5. **Coordinate Transformation:**
   - Graph region calibration
   - Pixel coordinates → audiogram values (frequency + dB)
   - Frequency mapping: 64Hz to 16kHz
   - Hearing loss range: 0-120 dB HL

**Confidence Scoring:**
The OCR confidence score (0.0-1.0) is calculated based on:
- Marker count (50% weight): Expected 9 measurements per ear
- Frequency coverage (25% weight): Unique frequencies found
- dB validity (25% weight): All values within 0-120 dB range

**Confidence Thresholds:**
- `≥ 0.80`: High confidence, auto-accepted
- `< 0.80`: Needs review, user prompted to verify/correct

---

## Data Models

### AudiogramMeasurement
```typescript
{
  frequency_hz: number   // Frequency in Hertz (e.g., 250, 500, 1000)
  threshold_db: number   // Hearing threshold in dB HL (0-120)
}
```

### HearingTest
```typescript
{
  id: string              // UUID
  test_date: string       // ISO 8601 date (YYYY-MM-DD)
  source_type: string     // "home" | "clinic" | "other"
  location: string        // Test location
  confidence: number      // OCR confidence (0.0-1.0)
}
```

### TestDetail (Full Test)
```typescript
{
  id: string
  test_date: string
  source_type: string
  location: string
  left_ear: AudiogramMeasurement[]
  right_ear: AudiogramMeasurement[]
  metadata: {
    device: string
    technician: string
    notes: string
    confidence?: number
    image_path?: string
  }
}
```

---

## Error Handling

All endpoints follow consistent error response format:

**Client Errors (4xx):**
```json
{
  "error": "Human-readable error message"
}
```

**Server Errors (5xx):**
```json
{
  "error": "Internal error message"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request succeeded
- `400 Bad Request`: Invalid request (missing fields, invalid format)
- `404 Not Found`: Resource doesn't exist
- `500 Internal Server Error`: Server-side processing error

---

## CORS

CORS is enabled for `http://localhost:3000` (frontend development server).

**Allowed Methods:** `GET`, `POST`, `PUT`, `DELETE`

**Allowed Headers:** `Content-Type`, `Authorization`

---

## Rate Limiting

Currently no rate limiting is implemented. This is a local desktop application with no network exposure.

---

## Testing

**Backend Tests:**
```bash
cd backend
PYTHONPATH=.. pytest tests/ -v
```

**Manual API Testing:**
```bash
# Single upload
curl -X POST http://localhost:5001/api/tests/upload \
  -F "file=@audiogram.jpeg"

# Bulk upload
curl -X POST http://localhost:5001/api/tests/bulk-upload \
  -F "files[]=@test1.jpeg" \
  -F "files[]=@test2.jpeg"

# List tests
curl http://localhost:5001/api/tests

# Get test details
curl http://localhost:5001/api/tests/{test_id}

# Delete test
curl -X DELETE http://localhost:5001/api/tests/{test_id}
```
