#!/usr/bin/env python3
"""
Import script for Jacoti audiogram images using Claude vision API.
Source: Hearing test Archive/Audiograms/*.jpeg
"""

import sqlite3
import uuid
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_utils import init_database
from backend.config import DB_PATH, DATA_DIR
from backend.ocr.claude_parser import parse_image_audiogram


def generate_uuid():
    return str(uuid.uuid4())


def insert_jacoti_test(conn, ocr_result, image_path):
    """Insert a Jacoti hearing test with Claude-extracted measurements."""
    cursor = conn.cursor()

    test_id = generate_uuid()

    # Extract metadata
    metadata = ocr_result.get('metadata', {})
    test_date = ocr_result.get('test_date')
    test_time = metadata.get('time')
    location = metadata.get('location', 'Unknown')
    device_name = metadata.get('device', 'Jacoti')
    confidence = ocr_result.get('confidence', 0.0)

    # If no date extracted, try to parse from filename (e.g., "2024-12-07.jpeg")
    if not test_date:
        filename = Path(image_path).stem
        try:
            # Try parsing YYYY-MM-DD format from filename
            datetime.strptime(filename, '%Y-%m-%d')
            test_date = filename
        except ValueError:
            # If that fails, use a placeholder or skip
            print(f"⚠ Warning: Could not extract date from {image_path.name}, skipping...")
            return None

    # Insert test record
    cursor.execute("""
        INSERT INTO hearing_test (
            id, test_date, test_time, source_type, location, device_name,
            technician_name, notes, image_path, ocr_confidence
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        test_id,
        test_date,
        test_time,
        'home',  # Jacoti is home testing device
        location,
        device_name,
        None,  # No technician for home tests
        f'Imported using Claude vision. Raw footer: {metadata.get("raw_footer_text", "")}',
        str(image_path),
        confidence
    ))

    # Insert measurements for both ears with deduplication
    for ear_name, ear_key in [('right', 'right_ear'), ('left', 'left_ear')]:
        ear_data = ocr_result.get(ear_key, [])

        # Deduplicate measurements by frequency - take median threshold if duplicates exist
        freq_groups = {}
        for measurement in ear_data:
            freq = measurement.get('frequency_hz')
            threshold = measurement.get('threshold_db')

            if freq is not None and threshold is not None:
                if freq not in freq_groups:
                    freq_groups[freq] = []
                freq_groups[freq].append(threshold)

        # Insert deduplicated measurements
        for freq, thresholds in freq_groups.items():
            # Take median threshold if multiple values for same frequency
            median_threshold = sorted(thresholds)[len(thresholds) // 2]

            cursor.execute("""
                INSERT INTO audiogram_measurement (
                    id, id_hearing_test, ear, frequency_hz, threshold_db, measurement_type
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                generate_uuid(),
                test_id,
                ear_name,
                freq,
                median_threshold,
                'air_conduction'
            ))

    conn.commit()
    print(f"✓ Imported: {test_date} - {location} (confidence: {confidence:.2f})")
    return test_id


def main():
    """Import all Jacoti audiogram images from the archive using Claude."""

    # Define source directories
    archive_root = Path(__file__).parent / 'Hearing test Archive'
    audiogram_dir = archive_root / 'Audiograms'

    if not archive_root.exists():
        print(f"Error: Directory not found: {archive_root}")
        return

    # Find all JPEG files from both directories
    image_files = []

    # Add files from Audiograms subdirectory
    if audiogram_dir.exists():
        image_files.extend(audiogram_dir.glob('*.jpeg'))
        image_files.extend(audiogram_dir.glob('*.jpg'))

    # Add files from archive root
    for pattern in ['*.jpeg', '*.jpg']:
        for file in archive_root.glob(pattern):
            if file.is_file():
                image_files.append(file)

    # Sort by filename
    image_files = sorted(set(image_files))

    if not image_files:
        print(f"No JPEG files found in {audiogram_dir}")
        return

    # Initialize database if needed
    if not DB_PATH.exists():
        print(f"Initializing database at {DB_PATH}...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        init_database(DB_PATH)
        print("✓ Database initialized\n")

    conn = sqlite3.connect(DB_PATH)

    print(f"\n{'='*60}")
    print(f"Importing {len(image_files)} Jacoti audiogram images")
    print(f"Using Claude vision API for extraction")
    print(f"Source: {archive_root}")
    print(f"{'='*60}\n")

    imported_count = 0
    failed_count = 0

    for image_path in image_files:
        try:
            print(f"Processing: {image_path.name}...", end=' ')
            ocr_result = parse_image_audiogram(image_path)
            test_id = insert_jacoti_test(conn, ocr_result, image_path)
            if test_id:
                imported_count += 1
        except Exception as e:
            failed_count += 1
            print(f"\n✗ Failed to process {image_path.name}: {e}\n")

    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Successfully imported {imported_count}/{len(image_files)} tests")
    if failed_count > 0:
        print(f"✗ Failed to import {failed_count} tests")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
