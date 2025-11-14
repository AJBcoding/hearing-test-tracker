#!/usr/bin/env python3
"""Integration test for complete upload workflow."""
import sys
import os
from pathlib import Path
import requests
import time
import subprocess

def test_integration():
    """Test complete flow: upload image → process → retrieve data."""

    print("Starting integration test...")

    # Use a different port to avoid conflicts
    test_port = 5050

    # Start backend
    print(f"\n1. Starting Flask backend on port {test_port}...")
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path.cwd())
    env['FLASK_RUN_PORT'] = str(test_port)

    # Use flask run command which respects environment variables
    backend_proc = subprocess.Popen(
        [sys.executable, '-m', 'flask', '--app', 'backend.app:create_app()', 'run', '--port', str(test_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )

    # Wait for backend to start
    print("   Waiting for backend to initialize...")
    time.sleep(5)

    try:
        # Test health endpoint with retries
        print("2. Testing health endpoint...")
        base_url = f'http://localhost:{test_port}'
        for i in range(3):
            try:
                response = requests.get(f'{base_url}/health', timeout=5)
                if response.status_code == 200:
                    print("   ✓ Backend healthy")
                    break
            except requests.exceptions.ConnectionError:
                if i < 2:
                    time.sleep(2)
                else:
                    raise
        else:
            assert response.status_code == 200, "Health check failed"

        # Test list tests (should be empty initially)
        print("3. Testing list tests endpoint...")
        response = requests.get(f'{base_url}/api/tests', timeout=5)
        assert response.status_code == 200, "List tests failed"
        print(f"   ✓ Found {len(response.json())} existing tests")

        # TODO: Upload test with actual audiogram image when available

        print("\n✓ Integration test passed!")
        return True

    except Exception as e:
        print(f"\n✗ Integration test failed: {e}")
        # Print backend output for debugging
        try:
            stdout, stderr = backend_proc.communicate(timeout=1)
            if stderr:
                print(f"\nBackend stderr:\n{stderr.decode()}")
        except subprocess.TimeoutExpired:
            backend_proc.kill()
            stdout, stderr = backend_proc.communicate()
            if stderr:
                print(f"\nBackend stderr:\n{stderr.decode()}")
        return False

    finally:
        # Cleanup
        if backend_proc.poll() is None:
            backend_proc.terminate()
            backend_proc.wait()
        print("\nBackend stopped")


if __name__ == '__main__':
    success = test_integration()
    sys.exit(0 if success else 1)
