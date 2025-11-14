"""Application configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
AUDIOGRAMS_DIR = DATA_DIR / "audiograms"
DB_PATH = DATA_DIR / "hearing_tests.db"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
AUDIOGRAMS_DIR.mkdir(exist_ok=True)

# OCR confidence threshold
OCR_CONFIDENCE_THRESHOLD = 0.8

# Audiometric standard frequencies (Hz)
STANDARD_FREQUENCIES = [64, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
