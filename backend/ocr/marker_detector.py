"""Detect audiogram data point markers using color-based segmentation."""
import cv2
import numpy as np
from typing import List, Dict, Literal


def detect_markers_by_color(
    image: np.ndarray,
    color: Literal['red', 'blue']
) -> List[Dict[str, int]]:
    """
    Detect audiogram markers by color.

    Args:
        image: BGR color image
        color: 'red' for right ear circles, 'blue' for left ear X markers

    Returns:
        List of marker positions: [{'x': int, 'y': int}, ...]
    """
    if color == 'red':
        return _detect_red_circles(image)
    elif color == 'blue':
        return _detect_blue_markers(image)
    else:
        raise ValueError(f"Invalid color: {color}")


def _detect_red_circles(image: np.ndarray) -> List[Dict[str, int]]:
    """
    Detect red circular markers.

    Args:
        image: BGR color image

    Returns:
        List of circle center positions
    """
    # Convert to HSV for better color isolation
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Red color range in HSV (red wraps around at 180)
    lower_red1 = np.array([0, 100, 100])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([170, 100, 100])
    upper_red2 = np.array([180, 255, 255])

    # Create mask for red pixels
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = cv2.bitwise_or(mask1, mask2)

    # Find contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    markers = []
    for contour in contours:
        # Calculate centroid
        M = cv2.moments(contour)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            markers.append({'x': cx, 'y': cy})

    return markers


def _detect_blue_markers(image: np.ndarray) -> List[Dict[str, int]]:
    """
    Detect blue X markers.

    Args:
        image: BGR color image

    Returns:
        List of X marker center positions
    """
    # Convert to HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Blue color range in HSV
    lower_blue = np.array([100, 100, 100])
    upper_blue = np.array([130, 255, 255])

    # Create mask for blue pixels
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Find contours
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    markers = []
    for contour in contours:
        # Calculate centroid
        M = cv2.moments(contour)
        if M['m00'] > 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            markers.append({'x': cx, 'y': cy})

    return markers
