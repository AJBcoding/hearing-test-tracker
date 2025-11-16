#!/usr/bin/env python3
"""Process clinical audiogram data from House Clinic and UCLA Health reports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_utils import get_connection, generate_uuid
from backend.config import DB_PATH

# Extracted clinical audiogram data from House Clinic and UCLA Health
audiograms = [
    # House Clinic/UCLA - Most recent test from 01/12/2024
    {
        "filename": "2025-04-12 - house ucla audiology hearing tests.pdf (Page 1)",
        "test_date": "2024-01-12",
        "test_time": None,
        "device": "House Clinic",
        "location": "House Ear Clinic",
        "right_ear": [
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 750, "threshold_db": 15},
            {"frequency_hz": 1000, "threshold_db": 15},
            {"frequency_hz": 1500, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 20},
            {"frequency_hz": 3000, "threshold_db": 20},
            {"frequency_hz": 4000, "threshold_db": 30},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 14},
        ],
        "left_ear": [
            {"frequency_hz": 250, "threshold_db": 45},
            {"frequency_hz": 500, "threshold_db": 40},
            {"frequency_hz": 750, "threshold_db": 15},
            {"frequency_hz": 1000, "threshold_db": 15},
            {"frequency_hz": 2000, "threshold_db": 15},
            {"frequency_hz": 3000, "threshold_db": 35},
            {"frequency_hz": 4000, "threshold_db": 40},
            {"frequency_hz": 6000, "threshold_db": 50},
            {"frequency_hz": 8000, "threshold_db": 40},
        ],
    },
    # House Clinic - 06/22/2022
    {
        "filename": "2025-04-12 - house ucla audiology hearing tests.pdf (Page 1)",
        "test_date": "2022-06-22",
        "test_time": None,
        "device": "House Clinic",
        "location": "House Ear Clinic",
        "right_ear": [
            {"frequency_hz": 250, "threshold_db": 20},
            {"frequency_hz": 500, "threshold_db": 15},
            {"frequency_hz": 1000, "threshold_db": 20},
            {"frequency_hz": 2000, "threshold_db": 25},
        ],
        "left_ear": [
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 15},
            {"frequency_hz": 2000, "threshold_db": 25},
            {"frequency_hz": 3000, "threshold_db": 35},
            {"frequency_hz": 4000, "threshold_db": 15},
        ],
    },
    # House Clinic - 06/06/2022
    {
        "filename": "2025-04-12 - house ucla audiology hearing tests.pdf (Page 1)",
        "test_date": "2022-06-06",
        "test_time": None,
        "device": "House Clinic",
        "location": "House Ear Clinic",
        "right_ear": [
            {"frequency_hz": 250, "threshold_db": 5},
            {"frequency_hz": 500, "threshold_db": 5},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 20},
            {"frequency_hz": 3000, "threshold_db": 15},
            {"frequency_hz": 4000, "threshold_db": 10},
        ],
        "left_ear": [
            {"frequency_hz": 250, "threshold_db": 5},
            {"frequency_hz": 500, "threshold_db": 5},
            {"frequency_hz": 1000, "threshold_db": 10},
            {"frequency_hz": 2000, "threshold_db": 20},
            {"frequency_hz": 3000, "threshold_db": 35},
            {"frequency_hz": 4000, "threshold_db": 10},
        ],
    },
    # UCLA Health - 10/16/2024
    {
        "filename": "2025-04-12 - house ucla audiology hearing tests.pdf (Pages 5-6)",
        "test_date": "2024-10-16",
        "test_time": None,
        "device": "GSI AudioStar Pro",
        "location": "UCLA 920 Westwood Blvd",
        "right_ear": [
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 15},
            {"frequency_hz": 2000, "threshold_db": 15},
            {"frequency_hz": 3000, "threshold_db": 20},
            {"frequency_hz": 4000, "threshold_db": 20},
            {"frequency_hz": 6000, "threshold_db": 30},
            {"frequency_hz": 8000, "threshold_db": 35},
        ],
        "left_ear": [
            {"frequency_hz": 250, "threshold_db": 55},
            {"frequency_hz": 500, "threshold_db": 55},
            {"frequency_hz": 1000, "threshold_db": 35},
            {"frequency_hz": 2000, "threshold_db": 25},
            {"frequency_hz": 3000, "threshold_db": 35},
            {"frequency_hz": 4000, "threshold_db": 40},
            {"frequency_hz": 6000, "threshold_db": 40},
            {"frequency_hz": 8000, "threshold_db": 50},
        ],
    },
    # UCLA Health - 05/23/2024
    {
        "filename": "2025-04-12 - house ucla audiology hearing tests.pdf (Pages 9-10)",
        "test_date": "2024-05-23",
        "test_time": None,
        "device": "GSI AudioStar Pro",
        "location": "UCLA 920 Westwood Blvd",
        "right_ear": [
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 15},
            {"frequency_hz": 2000, "threshold_db": 15},
            {"frequency_hz": 3000, "threshold_db": 20},
            {"frequency_hz": 4000, "threshold_db": 20},
            {"frequency_hz": 6000, "threshold_db": 30},
            {"frequency_hz": 8000, "threshold_db": 25},
        ],
        "left_ear": [
            {"frequency_hz": 250, "threshold_db": 10},
            {"frequency_hz": 500, "threshold_db": 10},
            {"frequency_hz": 1000, "threshold_db": 20},
            {"frequency_hz": 2000, "threshold_db": 20},
            {"frequency_hz": 3000, "threshold_db": 40},
            {"frequency_hz": 4000, "threshold_db": 45},
            {"frequency_hz": 6000, "threshold_db": 45},
            {"frequency_hz": 8000, "threshold_db": 50},
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
        'audiologist',
        data['location'],
        data['device'],
        image_path,
        1.0,  # High confidence - manually extracted by Claude
        f"Clinical audiogram data extracted by Claude Code vision"
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
    """Process all clinical audiograms and save to database."""
    print(f"Processing {len(audiograms)} clinical audiograms...\n")

    for i, data in enumerate(audiograms, 1):
        print(f"[{i}/{len(audiograms)}] Processing {data['test_date']} - {data['device']}...")
        print(f"  Location: {data['location']}")
        print(f"  Right ear: {len(data['right_ear'])} measurements")
        print(f"  Left ear: {len(data['left_ear'])} measurements")

        test_id = save_audiogram_to_db(data)
        print(f"  ✓ Saved with ID: {test_id}\n")

    print(f"✓ Successfully processed all {len(audiograms)} clinical audiograms")


if __name__ == '__main__':
    main()
