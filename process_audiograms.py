#!/usr/bin/env python3
"""Process audiogram images and save to database using Claude-extracted data."""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_utils import get_connection, generate_uuid
from backend.config import DB_PATH

# Extracted audiogram data from Claude Code vision analysis
audiograms = [
    {
        "filename": "2025-01-02 - Byrnes Hearing.jpeg",
        "test_date": "2025-01-06",
        "test_time": "12:43",
        "device": "Jacoti Hearing Center",
        "location": "Home",
        "right_ear": [
            {"frequency_hz": 125, "threshold_db": 20},
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 10},
            {"frequency_hz": 3000, "threshold_db": 10},
            {"frequency_hz": 4000, "threshold_db": 15},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 60},
            {"frequency_hz": 16000, "threshold_db": 80},
        ],
        "left_ear": [
            {"frequency_hz": 125, "threshold_db": 45},
            {"frequency_hz": 250, "threshold_db": 45},
            {"frequency_hz": 500, "threshold_db": 45},
            {"frequency_hz": 1000, "threshold_db": 50},
            {"frequency_hz": 1500, "threshold_db": 55},
            {"frequency_hz": 2000, "threshold_db": 55},
            {"frequency_hz": 3000, "threshold_db": 60},
            {"frequency_hz": 4000, "threshold_db": 65},
            {"frequency_hz": 6000, "threshold_db": 70},
            {"frequency_hz": 8000, "threshold_db": 80},
            {"frequency_hz": 16000, "threshold_db": 95},
        ],
    },
    {
        "filename": "2025-01-03 Hearing .jpeg",
        "test_date": "2025-01-06",
        "test_time": "12:42",
        "device": "Jacoti Hearing Center",
        "location": "Home",
        "right_ear": [
            {"frequency_hz": 125, "threshold_db": 10},
            {"frequency_hz": 250, "threshold_db": 15},
            {"frequency_hz": 500, "threshold_db": 15},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 10},
            {"frequency_hz": 3000, "threshold_db": 15},
            {"frequency_hz": 4000, "threshold_db": 20},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 50},
            {"frequency_hz": 16000, "threshold_db": 75},
        ],
        "left_ear": [
            {"frequency_hz": 125, "threshold_db": 40},
            {"frequency_hz": 250, "threshold_db": 40},
            {"frequency_hz": 500, "threshold_db": 45},
            {"frequency_hz": 1000, "threshold_db": 45},
            {"frequency_hz": 1500, "threshold_db": 50},
            {"frequency_hz": 2000, "threshold_db": 45},
            {"frequency_hz": 3000, "threshold_db": 55},
            {"frequency_hz": 4000, "threshold_db": 60},
            {"frequency_hz": 6000, "threshold_db": 65},
            {"frequency_hz": 8000, "threshold_db": 75},
            {"frequency_hz": 16000, "threshold_db": 85},
        ],
    },
    {
        "filename": "2025-01-04 Byrnes Hearing.jpeg",
        "test_date": "2025-01-06",
        "test_time": "12:42",
        "device": "Jacoti Hearing Center",
        "location": "Home",
        "right_ear": [
            {"frequency_hz": 125, "threshold_db": 20},
            {"frequency_hz": 250, "threshold_db": 15},
            {"frequency_hz": 500, "threshold_db": 15},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 10},
            {"frequency_hz": 3000, "threshold_db": 15},
            {"frequency_hz": 4000, "threshold_db": 20},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 50},
            {"frequency_hz": 16000, "threshold_db": 75},
        ],
        "left_ear": [
            {"frequency_hz": 125, "threshold_db": 35},
            {"frequency_hz": 250, "threshold_db": 40},
            {"frequency_hz": 500, "threshold_db": 35},
            {"frequency_hz": 1000, "threshold_db": 40},
            {"frequency_hz": 1500, "threshold_db": 45},
            {"frequency_hz": 2000, "threshold_db": 45},
            {"frequency_hz": 3000, "threshold_db": 55},
            {"frequency_hz": 4000, "threshold_db": 60},
            {"frequency_hz": 6000, "threshold_db": 65},
            {"frequency_hz": 8000, "threshold_db": 75},
            {"frequency_hz": 16000, "threshold_db": 85},
        ],
    },
    {
        "filename": "2025-01-06 - Byrnes Hearing.jpeg",
        "test_date": "2025-01-06",
        "test_time": "12:41",
        "device": "Jacoti Hearing Center",
        "location": "Home",
        "right_ear": [
            {"frequency_hz": 125, "threshold_db": 15},
            {"frequency_hz": 250, "threshold_db": 15},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 10},
            {"frequency_hz": 3000, "threshold_db": 15},
            {"frequency_hz": 4000, "threshold_db": 20},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 55},
            {"frequency_hz": 16000, "threshold_db": 80},
        ],
        "left_ear": [
            {"frequency_hz": 125, "threshold_db": 40},
            {"frequency_hz": 250, "threshold_db": 45},
            {"frequency_hz": 500, "threshold_db": 40},
            {"frequency_hz": 1000, "threshold_db": 40},
            {"frequency_hz": 1500, "threshold_db": 45},
            {"frequency_hz": 2000, "threshold_db": 50},
            {"frequency_hz": 3000, "threshold_db": 55},
            {"frequency_hz": 4000, "threshold_db": 60},
            {"frequency_hz": 6000, "threshold_db": 65},
            {"frequency_hz": 8000, "threshold_db": 75},
            {"frequency_hz": 16000, "threshold_db": 85},
        ],
    },
    {
        "filename": "2025-07-03 -Hearing Test .jpeg",
        "test_date": "2025-07-03",
        "test_time": "08:49",
        "device": "Jacoti Hearing Center",
        "location": "Home",
        "right_ear": [
            {"frequency_hz": 125, "threshold_db": 20},
            {"frequency_hz": 250, "threshold_db": 15},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 10},
            {"frequency_hz": 3000, "threshold_db": 15},
            {"frequency_hz": 4000, "threshold_db": 25},
            {"frequency_hz": 6000, "threshold_db": 25},
            {"frequency_hz": 8000, "threshold_db": 50},
            {"frequency_hz": 10000, "threshold_db": 60},
            {"frequency_hz": 16000, "threshold_db": 80},
        ],
        "left_ear": [
            {"frequency_hz": 64, "threshold_db": 70},
            {"frequency_hz": 125, "threshold_db": 55},
            {"frequency_hz": 250, "threshold_db": 55},
            {"frequency_hz": 500, "threshold_db": 45},
            {"frequency_hz": 1000, "threshold_db": 55},
            {"frequency_hz": 1500, "threshold_db": 60},
            {"frequency_hz": 2000, "threshold_db": 60},
            {"frequency_hz": 3000, "threshold_db": 65},
            {"frequency_hz": 4000, "threshold_db": 65},
            {"frequency_hz": 6000, "threshold_db": 70},
            {"frequency_hz": 8000, "threshold_db": 80},
            {"frequency_hz": 16000, "threshold_db": 95},
        ],
    },
]


def save_audiogram_to_db(data: dict) -> str:
    """Save audiogram data to database."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()

    # Create test record
    test_id = generate_uuid()
    image_path = f"Hearing test Archive/{data['filename']}"

    cursor.execute("""
        INSERT INTO hearing_test (
            id, test_date, source_type, location, device_name,
            image_path, ocr_confidence, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        data['test_date'],
        'home',
        data['location'],
        data['device'],
        image_path,
        1.0,  # High confidence - manually extracted by Claude
        f"Extracted by Claude Code vision at {data['test_time']}"
    ))

    # Insert measurements
    for ear_name, ear_data in [('right', data['right_ear']), ('left', data['left_ear'])]:
        for measurement in ear_data:
            cursor.execute("""
                INSERT INTO audiogram_measurement (
                    id, id_hearing_test, ear, frequency_hz, threshold_db
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                generate_uuid(),
                test_id,
                ear_name,
                measurement['frequency_hz'],
                measurement['threshold_db']
            ))

    conn.commit()
    conn.close()

    return test_id


def main():
    """Process all audiograms and save to database."""
    print(f"Processing {len(audiograms)} audiograms...\n")

    for i, data in enumerate(audiograms, 1):
        print(f"[{i}/{len(audiograms)}] Processing {data['filename']}...")
        print(f"  Date: {data['test_date']} {data['test_time']}")
        print(f"  Right ear: {len(data['right_ear'])} measurements")
        print(f"  Left ear: {len(data['left_ear'])} measurements")

        test_id = save_audiogram_to_db(data)
        print(f"  ✓ Saved with ID: {test_id}\n")

    print(f"✓ Successfully processed all {len(audiograms)} audiograms")


if __name__ == '__main__':
    main()
