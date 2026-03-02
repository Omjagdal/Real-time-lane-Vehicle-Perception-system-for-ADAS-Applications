"""
vehicle_detection.py
--------------------
YOLOv11n-based vehicle detection wrapper.

Filters detections to road vehicles only:
  car (2), motorcycle (3), bus (5), truck (7)  — COCO class IDs
"""

import os
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional

try:
    from ultralytics import YOLO
    _ULTRALYTICS_OK = True
except ImportError:
    _ULTRALYTICS_OK = False


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
VEHICLE_CLASSES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
DEFAULT_CONF    = 0.4
DEFAULT_IOU     = 0.45

# Candidate locations to look for the YOLO weights file.
# The first existing file wins; if none exist, Ultralytics auto-downloads.
_MODEL_CANDIDATES = [
    "models/yolo/yolov11n.pt",   # project local copy
    "models/yolo/yolo11n.pt",
    "yolo11n.pt",                 # Ultralytics default cache name
    "yolov8n.pt",                 # fallback if YOLO 11 not present
]

def _resolve_model() -> str:
    """Return the first existing weights path, or the Ultralytics download name."""
    for path in _MODEL_CANDIDATES:
        if os.path.isfile(path):
            return path
    return "yolo11n.pt"   # Ultralytics will download this automatically

DEFAULT_MODEL = _resolve_model()


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    """Single vehicle detection result."""
    bbox      : List[int]        # [x1, y1, x2, y2]  (pixel coords)
    class_id  : int
    label     : str
    confidence: float
    cx        : int = field(init=False)   # Centre X
    cy        : int = field(init=False)   # Centre Y
    width     : int = field(init=False)
    height    : int = field(init=False)

    def __post_init__(self):
        x1, y1, x2, y2 = self.bbox
        self.cx     = (x1 + x2) // 2
        self.cy     = (y1 + y2) // 2
        self.width  = x2 - x1
        self.height = y2 - y1


# ---------------------------------------------------------------------------
# Detector class
# ---------------------------------------------------------------------------

class VehicleDetector:
    """
    Wraps a YOLO model for vehicle-only detection.

    Parameters
    ----------
    model_path : Path to the YOLO weights file (.pt).
                 Will be downloaded automatically by Ultralytics on first use.
    conf       : Detection confidence threshold.
    iou        : Non-maximum suppression IoU threshold.
    device     : Inference device ('cpu', 'cuda', 'mps', etc.).
    """

    def __init__(self,
                 model_path: str  = DEFAULT_MODEL,
                 conf      : float = DEFAULT_CONF,
                 iou       : float = DEFAULT_IOU,
                 device    : str   = "cpu"):
        if not _ULTRALYTICS_OK:
            raise ImportError("ultralytics is not installed. Run: pip install ultralytics")

        self.conf   = conf
        self.iou    = iou
        self.device = device
        self._model = YOLO(model_path)
        self._model.to(device)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on *frame* (BGR uint8) and return vehicle detections.

        Returns
        -------
        List of Detection objects, one per detected vehicle.
        """
        results = self._model.predict(
            source=frame,
            conf=self.conf,
            iou=self.iou,
            verbose=False,
            device=self.device,
        )

        detections: List[Detection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                if cls_id not in VEHICLE_CLASSES:
                    continue

                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                conf_val = float(box.conf[0].item())

                detections.append(Detection(
                    bbox=[x1, y1, x2, y2],
                    class_id=cls_id,
                    label=VEHICLE_CLASSES[cls_id],
                    confidence=conf_val,
                ))

        return detections
