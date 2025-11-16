#!/usr/bin/env python3
"""
Import script for House Clinic and UCLA hearing tests using Claude PDF parsing.
Source: Hearing test Archive/2025-04-12 - house ucla audiology hearing tests.pdf
"""

import sqlite3
import uuid
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_utils import init_database
from backend.config import DB_PATH, DATA_DIR
from backend.ocr.claude_parser import parse_pdf_audiogram

# PDF path
PDF_PATH = Path(__file__).parent / 'Hearing test Archive' / '2025-04-12 - house ucla audiology hearing tests.pdf'


def generate_uuid():
    return str(uuid.uuid4())


def insert_test(conn, test_data):
    """Insert a complete hearing test with measurements."""
    cursor = conn.cursor()

    test_id = generate_uuid()

    # Insert test record
    cursor.execute("""
        INSERT INTO hearing_test (
            id, test_date, test_time, source_type, location, device_name,
            technician_name, notes, image_path, ocr_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        test_data['test_date'],
        test_data.get('test_time'),
        'audiologist',  # Professional tests
        test_data['location'],
        test_data.get('device_name', 'Unknown'),
        test_data.get('technician_name'),
        test_data.get('notes', 'Imported from PDF using Claude'),
        str(PDF_PATH),
        1.0  # Claude extraction, high confidence
    ))

    # Insert measurements
    for ear in ['left', 'right']:
        if ear in test_data:
            for freq, threshold in test_data[ear].items():
                if threshold is not None:
                    cursor.execute("""
                        INSERT INTO audiogram_measurement (
                            id, id_hearing_test, ear, frequency_hz, threshold_db, measurement_type
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        generate_uuid(),
                        test_id,
                        ear,
                        freq,
                        threshold,
                        'air_conduction'
                    ))

    # Insert bone conduction measurements if present
    for ear in ['left_bc', 'right_bc']:
        if ear in test_data:
            ear_name = ear.replace('_bc', '')
            for freq, threshold in test_data[ear].items():
                if threshold is not None:
                    cursor.execute("""
                        INSERT INTO audiogram_measurement (
                            id, id_hearing_test, ear, frequency_hz, threshold_db, measurement_type
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        generate_uuid(),
                        test_id,
                        ear_name,
                        freq,
                        threshold,
                        'bone_conduction'
                    ))

    conn.commit()
    print(f"✓ Imported test: {test_data['test_date']} - {test_data['location']}")
    return test_id


def main():
    """Import all tests from the PDF using Claude."""

    if not PDF_PATH.exists():
        print(f"Error: PDF not found: {PDF_PATH}")
        return

    print(f"\n{'='*60}")
    print(f"Parsing PDF using Claude...")
    print(f"Source: {PDF_PATH.name}")
    print(f"{'='*60}\n")

    # Parse PDF using Claude
    try:
        tests = parse_pdf_audiogram(PDF_PATH)
        print(f"✓ Claude extracted {len(tests)} tests from PDF\n")
    except Exception as e:
        print(f"✗ Error parsing PDF: {e}")
        return

    # Initialize database if needed
    if not DB_PATH.exists():
        print(f"Initializing database at {DB_PATH}...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        init_database(DB_PATH)
        print("✓ Database initialized\n")

    conn = sqlite3.connect(DB_PATH)

    print(f"{'='*60}")
    print(f"Importing {len(tests)} hearing tests to database")
    print(f"{'='*60}\n")

    for test in tests:
        insert_test(conn, test)

    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Successfully imported {len(tests)} tests!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
