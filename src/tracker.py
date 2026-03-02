"""
tracker.py
----------
IoU-based multi-object tracker with Hungarian-algorithm assignment.

Each detection is matched to an existing track by maximising IoU.
Unmatched detections start new tracks; tracks that exceed the
maximum age without a match are deleted.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
IOU_THRESHOLD     = 0.30   # Min IoU to consider a match
MAX_AGE           = 5      # Frames before a lost track is removed
MIN_HITS          = 2      # Frames before a track is flagged as confirmed


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class Track:
    """Active vehicle track."""
    track_id   : int
    bbox       : List[int]       # [x1, y1, x2, y2]
    class_id   : int
    label      : str
    age        : int = 0         # Total frames this track has existed
    hits       : int = 1         # Consecutive frames with a matched detection
    missed     : int = 0         # Consecutive frames without a match

    @property
    def confirmed(self) -> bool:
        return self.hits >= MIN_HITS

    @property
    def cx(self) -> int:
        return (self.bbox[0] + self.bbox[2]) // 2

    @property
    def cy(self) -> int:
        return (self.bbox[1] + self.bbox[3]) // 2

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


# ---------------------------------------------------------------------------
# IoU helper
# ---------------------------------------------------------------------------

def _iou(boxA: List[int], boxB: List[int]) -> float:
    """Compute Intersection-over-Union for two [x1,y1,x2,y2] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter   = inter_w * inter_h
    if inter == 0:
        return 0.0

    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    union = areaA + areaB - inter
    return inter / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Tracker class
# ---------------------------------------------------------------------------

class IoUTracker:
    """
    Frame-by-frame multi-object tracker.

    Usage
    -----
    tracker = IoUTracker()
    for frame in video:
        detections = detector.detect(frame)
        tracks = tracker.update(detections)
        for t in tracks:
            print(t.track_id, t.bbox, t.label)
    """

    def __init__(self,
                 iou_threshold: float = IOU_THRESHOLD,
                 max_age      : int   = MAX_AGE):
        self._iou_threshold = iou_threshold
        self._max_age       = max_age
        self._tracks        : List[Track] = []
        self._next_id       : int = 1

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def update(self, detections) -> List[Track]:
        """
        Match *detections* (list of Detection objects) to existing tracks,
        update track states, and return all confirmed active tracks.

        Parameters
        ----------
        detections : List of vehicle_detection.Detection objects.
        """
        # Age all existing tracks
        for t in self._tracks:
            t.age    += 1
            t.missed += 1

        if not detections:
            self._remove_dead_tracks()
            return [t for t in self._tracks if t.confirmed]

        # --- Hungarian assignment ----------------------------------------
        matched_track_ids, matched_det_ids = self._assign(detections)

        # Update matched tracks
        for tid, did in zip(matched_track_ids, matched_det_ids):
            det = detections[did]
            trk = next(t for t in self._tracks if t.track_id == tid)
            trk.bbox     = det.bbox
            trk.class_id = det.class_id
            trk.label    = det.label
            trk.hits    += 1
            trk.missed   = 0

        # Create new tracks for unmatched detections
        matched_det_set = set(matched_det_ids)
        for i, det in enumerate(detections):
            if i not in matched_det_set:
                self._tracks.append(Track(
                    track_id=self._next_id,
                    bbox=det.bbox,
                    class_id=det.class_id,
                    label=det.label,
                ))
                self._next_id += 1

        self._remove_dead_tracks()
        return [t for t in self._tracks if t.confirmed]

    def reset(self):
        self._tracks   = []
        self._next_id  = 1

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _assign(self, detections) -> Tuple[List[int], List[int]]:
        """Run Hungarian assignment; return (track_ids, det_indices)."""
        n_tracks = len(self._tracks)
        n_dets   = len(detections)

        if n_tracks == 0:
            return [], []

        # Build IoU cost matrix (we maximise IoU → minimise 1 - IoU)
        cost = np.zeros((n_tracks, n_dets), dtype=np.float32)
        for ti, trk in enumerate(self._tracks):
            for di, det in enumerate(detections):
                cost[ti, di] = 1.0 - _iou(trk.bbox, det.bbox)

        row_ind, col_ind = linear_sum_assignment(cost)

        matched_track_ids = []
        matched_det_ids   = []
        for ri, ci in zip(row_ind, col_ind):
            iou_val = 1.0 - cost[ri, ci]
            if iou_val >= self._iou_threshold:
                matched_track_ids.append(self._tracks[ri].track_id)
                matched_det_ids.append(ci)

        return matched_track_ids, matched_det_ids

    def _remove_dead_tracks(self):
        self._tracks = [t for t in self._tracks if t.missed <= self._max_age]
