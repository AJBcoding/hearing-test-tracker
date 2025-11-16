#!/usr/bin/env python3
"""Verify imported hearing test data."""

import sqlite3
from pathlib import Path
from backend.config import DB_PATH


def verify_import():
    """Verify all tests were imported correctly."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all tests
    cursor.execute("""
        SELECT id, test_date, location, technician_name
        FROM hearing_test
        ORDER BY test_date DESC
    """)
    tests = cursor.fetchall()

    print(f"\n{'='*70}")
    print(f"DATABASE VERIFICATION")
    print(f"{'='*70}\n")
    print(f"Total tests imported: {len(tests)}\n")

    for i, test in enumerate(tests, 1):
        print(f"{i}. {test['test_date']} - {test['location']}")
        if test['technician_name']:
            print(f"   Technician: {test['technician_name']}")

        # Get measurement count
        cursor.execute("""
            SELECT ear, measurement_type, COUNT(*) as count
            FROM audiogram_measurement
            WHERE id_hearing_test = ?
            GROUP BY ear, measurement_type
        """, (test['id'],))
        measurements = cursor.fetchall()

        for m in measurements:
            print(f"   {m['ear']} ear ({m['measurement_type']}): {m['count']} measurements")
        print()

    # Sample a few measurements to verify accuracy
    print(f"{'='*70}")
    print("SAMPLE DATA VERIFICATION")
    print(f"{'='*70}\n")

    # Verify 2024-01-12 House Clinic
    cursor.execute("""
        SELECT test_date, location, ear, frequency_hz, threshold_db, measurement_type
        FROM hearing_test ht
        JOIN audiogram_measurement am ON ht.id = am.id_hearing_test
        WHERE ht.test_date = '2024-01-12'
        ORDER BY ear, measurement_type, frequency_hz
    """)
    print("House Clinic 2024-01-12 Sample:")
    for row in cursor.fetchmany(5):
        print(f"  {row['ear']} ear, {row['frequency_hz']}Hz ({row['measurement_type']}): {row['threshold_db']}dB")
    print()

    # Verify UCLA 2024-10-16
    cursor.execute("""
        SELECT test_date, location, ear, frequency_hz, threshold_db, measurement_type
        FROM hearing_test ht
        JOIN audiogram_measurement am ON ht.id = am.id_hearing_test
        WHERE ht.test_date = '2024-10-16'
        ORDER BY ear, measurement_type, frequency_hz
    """)
    print("UCLA 2024-10-16 Sample:")
    for row in cursor.fetchmany(5):
        print(f"  {row['ear']} ear, {row['frequency_hz']}Hz ({row['measurement_type']}): {row['threshold_db']}dB")
    print()

    conn.close()

    print(f"{'='*70}")
    print("✓ Verification complete!")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    verify_import()
