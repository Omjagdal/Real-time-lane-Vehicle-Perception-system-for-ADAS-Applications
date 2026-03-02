"""
preprocessing.py
----------------
Video frame preprocessing utilities for the ADAS pipeline.
Handles resizing, colour conversion, normalisation and ROI masking.
"""

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TARGET_WIDTH  = 1280
TARGET_HEIGHT = 720


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def resize_frame(frame: np.ndarray,
                 width: int  = TARGET_WIDTH,
                 height: int = TARGET_HEIGHT) -> np.ndarray:
    """Resize *frame* to (width × height) using inter-linear interpolation."""
    return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)


def normalize_frame(frame: np.ndarray) -> np.ndarray:
    """Normalize pixel values to [0, 1] (float32)."""
    return frame.astype(np.float32) / 255.0


def to_rgb(frame: np.ndarray) -> np.ndarray:
    """Convert a BGR frame (OpenCV default) to RGB."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def to_gray(frame: np.ndarray) -> np.ndarray:
    """Convert a BGR frame to single-channel greyscale."""
    return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)


def apply_gaussian_blur(frame: np.ndarray,
                        kernel_size: int = 5) -> np.ndarray:
    """Apply Gaussian blur for noise reduction before edge detection."""
    ksize = (kernel_size, kernel_size)
    return cv2.GaussianBlur(frame, ksize, 0)


def get_roi_mask(frame: np.ndarray) -> np.ndarray:
    """
    Build a trapezoidal Region-of-Interest mask that covers the lower
    portion of the frame where lanes are typically visible.

    Returns an 8-bit mask (255 = keep, 0 = discard).
    """
    h, w = frame.shape[:2]
    # Trapezoid vertices (bottom-left, top-left, top-right, bottom-right)
    vertices = np.array([[
        (int(w * 0.05), h),
        (int(w * 0.40), int(h * 0.58)),
        (int(w * 0.60), int(h * 0.58)),
        (int(w * 0.95), h),
    ]], dtype=np.int32)

    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    cv2.fillPoly(mask, vertices, 255)
    return mask


def apply_roi(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Bitwise-AND *frame* with the provided mask to keep only the ROI."""
    return cv2.bitwise_and(frame, frame, mask=mask)


def preprocess_for_detection(frame: np.ndarray) -> np.ndarray:
    """
    Full preprocessing chain for YOLO vehicle detection.

    Returns the resized BGR frame (YOLO expects BGR uint8).
    """
    return resize_frame(frame)


def preprocess_for_lane(frame: np.ndarray) -> np.ndarray:
    """
    Full preprocessing chain for lane detection.

    Returns a masked edge image (uint8, single-channel).
    """
    resized = resize_frame(frame)
    gray    = to_gray(resized)
    blurred = apply_gaussian_blur(gray, kernel_size=5)
    edges   = cv2.Canny(blurred, threshold1=50, threshold2=150)
    mask    = get_roi_mask(edges)
    return apply_roi(edges, mask)
