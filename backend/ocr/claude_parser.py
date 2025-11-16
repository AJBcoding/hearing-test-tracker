"""Parse audiograms using Claude's multimodal capabilities."""
import base64
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import anthropic


def parse_pdf_audiogram(pdf_path: Path) -> List[Dict]:
    """
    Parse audiogram PDF using Claude's native PDF reading.

    Args:
        pdf_path: Path to PDF file containing audiograms

    Returns:
        List of test dictionaries with extracted data:
        [{
            'test_date': str,  # YYYY-MM-DD format
            'location': str,
            'technician_name': str,
            'device_name': str,
            'notes': str,
            'right': {freq_hz: threshold_db, ...},  # Air conduction
            'left': {freq_hz: threshold_db, ...},   # Air conduction
            'right_bc': {freq_hz: threshold_db, ...},  # Bone conduction
            'left_bc': {freq_hz: threshold_db, ...}   # Bone conduction
        }, ...]
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Read PDF file as bytes
    with open(pdf_path, 'rb') as f:
        pdf_data = base64.standard_b64encode(f.read()).decode('utf-8')

    # Prompt Claude to extract structured audiogram data
    prompt = """Analyze this audiogram PDF and extract ALL hearing tests into structured JSON format.

For each test found in the PDF, extract:
1. test_date (YYYY-MM-DD format)
2. location (clinic/facility name)
3. technician_name (audiologist name if present)
4. device_name (equipment used)
5. notes (any additional information, signatures, etc.)
6. right (air conduction measurements for right ear as {frequency_hz: threshold_db})
7. left (air conduction measurements for left ear as {frequency_hz: threshold_db})
8. right_bc (bone conduction measurements for right ear, if present)
9. left_bc (bone conduction measurements for left ear, if present)

IMPORTANT:
- Extract ALL tests from the PDF (including historical/comparison data)
- Use integer frequencies (125, 250, 500, 750, 1000, 1500, 2000, 3000, 4000, 6000, 8000)
- Use integer or float threshold values in dB
- If a measurement is missing/empty, use null
- Return a JSON array of test objects

Example output format:
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

Return ONLY the JSON array, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_data,
                    },
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ],
        }],
    )

    # Parse Claude's response
    response_text = message.content[0].text

    # Extract JSON from response (handle potential markdown code blocks)
    if '```json' in response_text:
        json_start = response_text.find('```json') + 7
        json_end = response_text.find('```', json_start)
        response_text = response_text[json_start:json_end].strip()
    elif '```' in response_text:
        json_start = response_text.find('```') + 3
        json_end = response_text.find('```', json_start)
        response_text = response_text[json_start:json_end].strip()

    tests = json.loads(response_text)

    # Convert string keys to integers for frequency measurements
    for test in tests:
        for ear_key in ['right', 'left', 'right_bc', 'left_bc']:
            if ear_key in test and test[ear_key]:
                test[ear_key] = {
                    int(freq): threshold
                    for freq, threshold in test[ear_key].items()
                }

    return tests


def parse_image_audiogram(image_path: Path) -> Dict:
    """
    Parse Jacoti audiogram image using Claude's vision capabilities.

    Args:
        image_path: Path to JPEG image of Jacoti audiogram

    Returns:
        Dictionary with extracted data:
        {
            'test_date': str,  # YYYY-MM-DD format
            'left_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'right_ear': [{'frequency_hz': int, 'threshold_db': float}, ...],
            'metadata': {'location': str, 'device': str, 'time': str},
            'confidence': float  # 0.0-1.0
        }
    """
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.Anthropic(api_key=api_key)

    # Determine media type from extension
    suffix = image_path.suffix.lower()
    media_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.webp': 'image/webp'
    }
    media_type = media_type_map.get(suffix, 'image/jpeg')

    # Read image file as bytes
    with open(image_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    # Prompt Claude to extract audiogram measurements
    prompt = """Analyze this Jacoti audiogram image and extract all hearing threshold measurements.

The image shows two audiograms:
- Right ear (typically marked with circles/O in red/orange)
- Left ear (typically marked with X in blue)

Extract:
1. test_date from the footer (format: YYYY-MM-DD)
2. time from the footer (HH:MM format)
3. For each ear, extract ALL visible data points with:
   - frequency_hz (125, 250, 500, 1000/1k, 2000/2k, 4000/4k, 8000/8k, 16000/16k)
   - threshold_db (approximate dB value from y-axis, typically 0-120 range)

Return JSON in this exact format:
{
  "test_date": "YYYY-MM-DD",
  "metadata": {
    "time": "HH:MM",
    "device": "Jacoti",
    "location": "Home",
    "raw_footer_text": "full footer text"
  },
  "right_ear": [
    {"frequency_hz": 125, "threshold_db": 25.0},
    {"frequency_hz": 250, "threshold_db": 15.0}
  ],
  "left_ear": [
    {"frequency_hz": 125, "threshold_db": 70.0},
    {"frequency_hz": 250, "threshold_db": 65.0}
  ],
  "confidence": 0.95
}

IMPORTANT:
- Read the threshold values carefully from the y-axis grid
- Include ALL visible data points for both ears
- Use standard audiogram frequencies
- Set confidence to 0.9-1.0 if the image is clear, 0.5-0.8 if partially obscured

Return ONLY the JSON object, no additional text."""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ],
        }],
    )

    # Parse Claude's response
    response_text = message.content[0].text

    # Extract JSON from response
    if '```json' in response_text:
        json_start = response_text.find('```json') + 7
        json_end = response_text.find('```', json_start)
        response_text = response_text[json_start:json_end].strip()
    elif '```' in response_text:
        json_start = response_text.find('```') + 3
        json_end = response_text.find('```', json_start)
        response_text = response_text[json_start:json_end].strip()

    result = json.loads(response_text)
    return result
