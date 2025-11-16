#!/usr/bin/env python3
"""Verify database contents after importing audiogram data."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.database.db_utils import get_connection
from backend.config import DB_PATH


def main():
    """Query and display database contents."""
    conn = get_connection(DB_PATH)
    cursor = conn.cursor()

    # Count total tests
    cursor.execute("SELECT COUNT(*) FROM hearing_test")
    total_tests = cursor.fetchone()[0]
    print(f"Total tests in database: {total_tests}\n")

    # Count by source type
    cursor.execute("""
        SELECT source_type, COUNT(*) as count
        FROM hearing_test
        GROUP BY source_type
    """)
    print("Tests by source type:")
    for source_type, count in cursor.fetchall():
        print(f"  {source_type}: {count}")
    print()

    # Count by device
    cursor.execute("""
        SELECT device_name, COUNT(*) as count
        FROM hearing_test
        GROUP BY device_name
        ORDER BY count DESC
    """)
    print("Tests by device:")
    for device, count in cursor.fetchall():
        print(f"  {device}: {count}")
    print()

    # List all tests
    cursor.execute("""
        SELECT test_date, device_name, location, source_type
        FROM hearing_test
        ORDER BY test_date DESC
    """)
    print("All tests (sorted by date):")
    print(f"{'Date':<12} {'Device':<25} {'Location':<30} {'Source':<15}")
    print("-" * 85)
    for test_date, device, location, source in cursor.fetchall():
        print(f"{test_date:<12} {device:<25} {location:<30} {source:<15}")
    print()

    # Count total measurements
    cursor.execute("SELECT COUNT(*) FROM audiogram_measurement")
    total_measurements = cursor.fetchone()[0]
    print(f"Total audiogram measurements: {total_measurements}")

    # Count measurements per ear
    cursor.execute("""
        SELECT ear, COUNT(*) as count
        FROM audiogram_measurement
        GROUP BY ear
    """)
    print("\nMeasurements by ear:")
    for ear, count in cursor.fetchall():
        print(f"  {ear}: {count}")

    conn.close()


if __name__ == '__main__':
    main()
