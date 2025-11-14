"""Start both backend and frontend servers."""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def main():
    base_dir = Path(__file__).parent
    venv_python = base_dir / 'venv' / 'bin' / 'python'

    # Start backend
    backend_process = subprocess.Popen(
        [str(venv_python), 'backend/app.py'],
        cwd=base_dir
    )

    # Wait for backend to start
    time.sleep(2)

    # Start frontend
    frontend_process = subprocess.Popen(
        ['npm', 'run', 'dev'],
        cwd=base_dir / 'frontend'
    )

    # Wait for frontend to start
    time.sleep(3)

    # Open browser
    webbrowser.open('http://localhost:3000')

    try:
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        backend_process.terminate()
        frontend_process.terminate()


if __name__ == '__main__':
    main()
