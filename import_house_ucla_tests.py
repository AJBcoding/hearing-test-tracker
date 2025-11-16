#!/usr/bin/env python3
"""
One-time import script for House Clinic and UCLA hearing tests from PDF.
Source: Hearing test Archive/2025-04-12 - house ucla audiology hearing tests.pdf
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
        test_data.get('notes', 'Imported from PDF'),
        str(PDF_PATH),
        1.0  # Manual entry, high confidence
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
    """Import all tests from the PDF."""

    # Define all tests with their data
    tests = []

    # ========== HOUSE CLINIC - 01/12/2024 (Main Test) ==========
    tests.append({
        'test_date': '2024-01-12',
        'location': 'House Clinic',
        'technician_name': 'William H. Slattery MD',
        'notes': 'Signed by: William H. Slattery MD, 1245 Wilshire Blvd, Los Angeles CA 90017-5809',
        'right': {  # Air Conduction
            125: 10,
            250: 10,
            500: 15,
            750: 15,
            1500: 10,
            2000: 20,
            3000: 20,
            4000: 30,
            6000: 40,
            8000: 14
        },
        'left': {  # Air Conduction
            250: 45,
            500: 40,
            750: 15,
            1000: 15,
            1500: 15,
            2000: 35,
            3000: 40,
            4000: 50,
            6000: 40,
            8000: 26
        },
        'right_bc': {  # Bone Conduction - mostly empty for this test
            500: 60
        },
        'left_bc': {  # Bone Conduction
            2000: 70,
            3000: 70
        }
    })

    # ========== HOUSE CLINIC - Historical Tests (from comparison tables) ==========

    # 06/21/2023
    tests.append({
        'test_date': '2023-06-21',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 10,
            250: 10,
            500: None,  # Empty in table
            750: 15,
            1000: None,
            1500: 15,
            2000: 35,
            3000: 30,
            4000: 40,
            6000: 50,
            8000: 18
        },
        'left': {
            125: None,
            250: 10,
            500: 10,
            750: None,
            1000: None,
            1500: 20,
            2000: None,
            3000: 20,
            4000: 35,
            6000: 45,
            8000: 21
        },
        'right_bc': {
            250: 0,
            500: 5,
            1000: 15,
            2000: 30,
            3000: 25
        },
        'left_bc': {
            250: 0,
            500: 10,
            1000: 15,
            2000: 30,
            3000: 45
        }
    })

    # 05/22/2023
    tests.append({
        'test_date': '2023-05-22',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 10,
            250: 10,
            500: None,
            750: 10,
            1000: None,
            1500: 15,
            2000: 30,
            3000: 25,
            4000: 40,
            6000: 45,
            8000: 16
        },
        'left': {
            125: None,
            250: 50,
            500: 45,
            750: None,
            1000: None,
            1500: 30,
            2000: None,
            3000: 35,
            4000: 45,
            6000: 50,
            8000: 38
        },
        'right_bc': {
            250: 5,
            500: 5,
            1000: 15,
            2000: 30,
            3000: 25
        },
        'left_bc': {
            250: None,
            500: 25,
            1000: 35,
            2000: 35,
            3000: 45
        }
    })

    # 02/27/2023
    tests.append({
        'test_date': '2023-02-27',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 10,
            250: 15,
            500: None,
            750: 15,
            1000: None,
            1500: 20,
            2000: 40,
            3000: 25,
            4000: 40,
            6000: 45,
            8000: 22
        },
        'left': {
            125: None,
            250: 5,
            500: 10,
            750: None,
            1000: None,
            1500: 25,
            2000: None,
            3000: 30,
            4000: 45,
            6000: 45,
            8000: 27
        },
        'right_bc': {
            250: 10,
            500: 10,
            1000: 20,
            2000: 35,
            3000: 25
        },
        'left_bc': {
            250: 10,
            500: 20,
            1000: 20,
            2000: 35,
            3000: 45
        }
    })

    # 11/16/2022
    tests.append({
        'test_date': '2022-11-16',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 30,
            250: 20,
            500: None,
            750: 15,
            1000: None,
            1500: 20,
            2000: 35,
            3000: 25,
            4000: 35,
            6000: 50,
            8000: 17
        },
        'left': {
            125: None,
            250: 50,
            500: 40,
            750: None,
            1000: None,
            1500: 30,
            2000: None,
            3000: 35,
            4000: 45,
            6000: 45,
            8000: 37
        },
        'right_bc': {
            250: 15,
            500: 5,
            1000: 20,
            2000: 35,
            3000: 25
        },
        'left_bc': {
            250: None,
            500: 20,
            1000: 35,
            2000: 35,
            3000: 45
        }
    })

    # 07/06/2022
    tests.append({
        'test_date': '2022-07-06',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 10,
            250: 10,
            500: None,
            750: 10,
            1000: None,
            1500: 10,
            2000: 15,
            3000: 15,
            4000: 35,
            6000: 45,
            8000: 11
        },
        'left': {
            125: None,
            250: 10,
            500: 5,
            750: 5,
            1000: 10,
            1500: None,
            2000: None,
            3000: 10,
            4000: 35,
            6000: 35,
            8000: 15
        },
        'right_bc': {
            250: 5,
            500: 0,
            1000: 5,
            2000: 10,
            3000: 15
        },
        'left_bc': {
            250: None,
            500: 0,
            1000: None,
            2000: 25,
            3000: 30
        }
    })

    # 06/22/2022
    tests.append({
        'test_date': '2022-06-22',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 45,
            250: 45,
            500: 35,
            750: 25,
            1000: None,
            1500: 15,
            2000: 30,
            3000: 25,
            4000: 35,
            6000: 40,
            8000: 29
        },
        'left': {
            125: None,
            250: 5,
            500: 10,
            750: 10,
            1000: 10,
            1500: None,
            2000: None,
            3000: 15,
            4000: 35,
            6000: 35,
            8000: 18
        },
        'right_bc': {
            250: 45,
            500: 20,
            1000: 15,
            2000: 20,
            3000: 25
        },
        'left_bc': {
            250: 10,
            500: 10,
            1000: 15,
            2000: 25,
            3000: 35
        }
    })

    # 06/06/2022
    tests.append({
        'test_date': '2022-06-06',
        'location': 'House Clinic',
        'notes': 'Historical data from comparison table',
        'right': {
            125: 10,
            250: 10,
            500: None,
            750: 15,
            1000: None,
            1500: 10,
            2000: 20,
            3000: 15,
            4000: 25,
            6000: 25,
            8000: 13
        },
        'left': {
            125: None,
            250: 10,
            500: 5,
            750: None,
            1000: 10,
            1500: None,
            2000: None,
            3000: 15,
            4000: 30,
            6000: 35,
            8000: 15
        },
        'right_bc': {
            250: 5,
            500: 5,
            1000: 10,
            2000: 20,
            3000: 15
        },
        'left_bc': {
            250: 5,
            500: 5,
            1000: 10,
            2000: 20,
            3000: 35
        }
    })

    # ========== UCLA HEALTH - 10/16/2024 ==========
    tests.append({
        'test_date': '2024-10-16',
        'location': 'UCLA 920 Westwood Blvd',
        'technician_name': 'Kathryn Sullivan, AuD',
        'notes': 'e-signed by Kathryn Sullivan, AuD, LIC# AU1542',
        'right': {  # Air Conduction
            250: 10,
            500: 10,
            1000: 15,
            2000: 15,
            3000: 20,
            4000: 20,
            6000: 30,
            8000: 35
        },
        'left': {  # Air Conduction
            250: 55,
            500: 55,
            1000: 35,
            2000: 25,
            3000: 35,
            4000: 40,
            6000: 40,
            8000: 50
        },
        'right_bc': {  # Bone Conduction
            500: 0,
            1000: 5,
            2000: 15,
            4000: 25
        },
        'left_bc': {  # Bone Conduction
            500: 45,
            1000: 25,
            4000: 30
        }
    })

    # ========== UCLA HEALTH - 05/23/2024 ==========
    tests.append({
        'test_date': '2024-05-23',
        'location': 'UCLA 920 Westwood Blvd',
        'technician_name': 'Maureen Virts, AuD',
        'notes': 'e-signed by Maureen Virts, AuD, LIC# AU3596',
        'right': {  # Air Conduction
            250: 10,
            500: 10,
            1000: 15,
            2000: 15,
            3000: 20,
            4000: 20,
            6000: 30,
            8000: 25
        },
        'left': {  # Air Conduction
            250: 10,
            500: 10,
            1000: 20,
            2000: 20,
            3000: 40,
            4000: 45,
            6000: 45,
            8000: 50
        },
        'right_bc': {  # Bone Conduction
            500: 10,
            1000: 10,
            2000: 15,
            4000: 25
        },
        'left_bc': {  # Bone Conduction - appears mostly empty/not visible
            4000: 45
        }
    })

    # Initialize database if needed
    if not DB_PATH.exists():
        print(f"Initializing database at {DB_PATH}...")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        init_database(DB_PATH)
        print("✓ Database initialized\n")

    conn = sqlite3.connect(DB_PATH)

    print(f"\n{'='*60}")
    print(f"Importing {len(tests)} hearing tests from PDF")
    print(f"Source: {PDF_PATH.name}")
    print(f"{'='*60}\n")

    for test in tests:
        insert_test(conn, test)

    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Successfully imported {len(tests)} tests!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
