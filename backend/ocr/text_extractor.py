"""OCR text extraction for audiogram metadata."""
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
import cv2
import pytesseract
from PIL import Image
import numpy as np


def extract_footer_region(image: np.ndarray) -> np.ndarray:
    """
    Extract the footer region from the audiogram image.

    For Jacoti audiograms, the footer is typically in the bottom 10% of the image.

    Args:
        image: Full audiogram image (BGR format)

    Returns:
        Cropped footer region
    """
    height, width = image.shape[:2]
    footer_height = int(height * 0.1)  # Bottom 10%
    footer_region = image[height - footer_height:height, 0:width]
    return footer_region


def preprocess_for_ocr(region: np.ndarray) -> np.ndarray:
    """
    Preprocess image region for better OCR accuracy.

    Args:
        region: Image region to preprocess

    Returns:
        Preprocessed image optimized for OCR
    """
    # Convert to grayscale
    gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

    # Apply slight blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Apply adaptive thresholding for better text contrast
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Invert if background is dark
    if np.mean(thresh) < 127:
        thresh = cv2.bitwise_not(thresh)

    return thresh


def extract_text_from_region(region: np.ndarray) -> str:
    """
    Extract text from an image region using Tesseract OCR.

    Args:
        region: Image region to extract text from

    Returns:
        Extracted text string
    """
    # Preprocess the region
    processed = preprocess_for_ocr(region)

    # Convert to PIL Image for pytesseract
    pil_image = Image.fromarray(processed)

    # Extract text with custom config for better accuracy
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(pil_image, config=custom_config)

    return text.strip()


def parse_jacoti_footer(footer_text: str) -> Optional[Dict[str, str]]:
    """
    Parse Jacoti audiogram footer text to extract metadata.

    Expected format: "Made with Jacoti Hearing Center - 2024-12-17 12:24"

    Args:
        footer_text: Raw footer text from OCR

    Returns:
        Dictionary with parsed metadata or None if parsing failed
        {
            'date': '2024-12-17',
            'time': '12:24',
            'device': 'Jacoti Hearing Center',
            'location': 'Jacoti Hearing Center'
        }
    """
    # Pattern to match Jacoti footer format
    # Flexible pattern to handle OCR variations
    pattern = r'Made with\s+(.+?)\s*[-–]\s*(\d{4}[-/]\d{2}[-/]\d{2})\s+(\d{1,2}:\d{2})'

    match = re.search(pattern, footer_text, re.IGNORECASE)

    if match:
        device = match.group(1).strip()
        date = match.group(2).replace('/', '-')  # Normalize date format
        time = match.group(3)

        return {
            'date': date,
            'time': time,
            'device': device,
            'location': device
        }

    # Fallback: Try to extract just date if footer pattern doesn't match
    date_pattern = r'(\d{4}[-/]\d{2}[-/]\d{2})'
    date_match = re.search(date_pattern, footer_text)

    if date_match:
        return {
            'date': date_match.group(1).replace('/', '-'),
            'time': None,
            'device': 'Unknown',
            'location': 'Unknown'
        }

    return None


def extract_jacoti_metadata(image_path: Path) -> Dict[str, Optional[str]]:
    """
    Extract metadata from Jacoti audiogram image.

    Args:
        image_path: Path to Jacoti audiogram image

    Returns:
        Dictionary with extracted metadata:
        {
            'date': str or None,
            'time': str or None,
            'device': str or None,
            'location': str or None,
            'raw_footer_text': str  # For debugging
        }
    """
    # Load image
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Cannot read image: {image_path}")

    # Extract footer region
    footer_region = extract_footer_region(image)

    # Extract text from footer
    footer_text = extract_text_from_region(footer_region)

    # Parse the footer text
    parsed_metadata = parse_jacoti_footer(footer_text)

    # Return metadata with raw text for debugging
    result = {
        'date': None,
        'time': None,
        'device': None,
        'location': None,
        'raw_footer_text': footer_text
    }

    if parsed_metadata:
        result.update(parsed_metadata)

    return result


def extract_header_text(image: np.ndarray) -> str:
    """
    Extract header text from the audiogram (e.g., "My audiogram").

    Args:
        image: Full audiogram image

    Returns:
        Extracted header text
    """
    height, width = image.shape[:2]
    header_height = int(height * 0.1)  # Top 10%
    header_region = image[0:header_height, 0:width]

    return extract_text_from_region(header_region)
