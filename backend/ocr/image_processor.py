"""Image preprocessing for OCR pipeline."""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict


def preprocess_image(image_path: Path) -> np.ndarray:
    """
    Preprocess audiogram image for OCR.

    Steps:
    1. Load image with OpenCV
    2. Convert to grayscale
    3. Apply adaptive thresholding for contrast
    4. Deskew if rotated

    Args:
        image_path: Path to JPEG audiogram image

    Returns:
        Preprocessed grayscale image as numpy array
    """
    # Load image
    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Cannot read image at {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Deskew (detect and correct rotation)
    processed = _deskew_image(processed)

    return processed


def _deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Detect and correct image rotation.

    Args:
        image: Grayscale image

    Returns:
        Deskewed image
    """
    # Detect edges
    edges = cv2.Canny(image, 50, 150, apertureSize=3)

    # Detect lines using Hough transform
    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        return image

    # Calculate average angle
    angles = []
    for rho, theta in lines[:, 0]:
        angle = np.rad2deg(theta) - 90
        angles.append(angle)

    median_angle = np.median(angles)

    # Only rotate if angle is significant (> 0.5 degrees)
    if abs(median_angle) < 0.5:
        return image

    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def extract_graph_region(image: np.ndarray) -> Dict[str, int]:
    """
    Identify the graph region boundaries within the image.

    Args:
        image: Preprocessed grayscale image

    Returns:
        Dictionary with graph bounds: {x_min, x_max, y_min, y_max}
    """
    # Find contours of white regions
    contours, _ = cv2.findContours(
        image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        # Fallback: use entire image
        h, w = image.shape[:2]
        return {'x_min': 0, 'x_max': w, 'y_min': 0, 'y_max': h}

    # Find largest contour (likely the graph)
    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)

    return {
        'x_min': x,
        'x_max': x + w,
        'y_min': y,
        'y_max': y + h
    }
