"""
speed.py
--------
Speed estimation for tracked vehicles using frame-to-frame position delta.

Approach:
  - Record the (cx, cy) centre of each track per frame.
  - Convert pixel displacement to metres using distance & frame geometry.
  - Apply exponential moving average (EMA) smoothing.
  - Return speed in km/h.
"""

import numpy as np
from collections import defaultdict, deque
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Pixels-per-metre at a reference distance.  Adjust as needed.
# At 10 m with focal=850 and car width=1.8 m → ~153 px/m
PIXELS_PER_METRE_AT_REF = 153.0
REFERENCE_DISTANCE_M    = 10.0

EMA_ALPHA    = 0.4    # Smoothing factor (higher = more reactive)
HISTORY_LEN  = 10     # Frames of position history to keep
FPS_DEFAULT  = 30.0   # Used as default when caller doesn't pass FPS


# ---------------------------------------------------------------------------
# SpeedEstimator class
# ---------------------------------------------------------------------------

class SpeedEstimator:
    """
    Stateful per-track speed estimator.

    Usage
    -----
    estimator = SpeedEstimator(fps=30)
    for frame in video:
        distances = {track_id: dist_m, ...}
        speeds    = estimator.update(tracks, distances)
        # speeds → {track_id: speed_kmh}
    """

    def __init__(self, fps: float = FPS_DEFAULT):
        self._fps           = max(fps, 1.0)
        self._positions     : Dict[int, deque]  = defaultdict(lambda: deque(maxlen=HISTORY_LEN))
        self._smooth_speed  : Dict[int, float]  = {}

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def update(self,
               tracks,
               distances: Dict[int, float]) -> Dict[int, float]:
        """
        Estimate speed for all active tracks.

        Parameters
        ----------
        tracks    : List of tracker.Track objects.
        distances : dict {track_id → distance_in_metres} from DistanceEstimator.

        Returns
        -------
        dict : {track_id: speed_kmh}
        """
        result: Dict[int, float] = {}
        active_ids = {t.track_id for t in tracks}

        for track in tracks:
            tid  = track.track_id
            dist = distances.get(tid, REFERENCE_DISTANCE_M)

            # Store centre position
            self._positions[tid].append((track.cx, track.cy))
            pos_hist = self._positions[tid]

            if len(pos_hist) < 2:
                result[tid] = 0.0
                continue

            # Pixel displacement over last two frames
            px1, py1 = pos_hist[-2]
            px2, py2 = pos_hist[-1]
            pixel_disp = np.hypot(px2 - px1, py2 - py1)

            # Scale factor: pixels_per_metre varies with distance
            scale = PIXELS_PER_METRE_AT_REF * (REFERENCE_DISTANCE_M / max(dist, 1.0))
            disp_m = pixel_disp / max(scale, 0.01)

            # speed m/s → km/h
            speed_kmh = disp_m * self._fps * 3.6

            # EMA smoothing
            prev = self._smooth_speed.get(tid, 0.0)
            smoothed = EMA_ALPHA * speed_kmh + (1.0 - EMA_ALPHA) * prev
            smoothed = float(np.clip(smoothed, 0.0, 250.0))

            self._smooth_speed[tid] = smoothed
            result[tid] = smoothed

        # Purge stale track data
        stale_ids = set(self._positions.keys()) - active_ids
        for sid in stale_ids:
            self._positions.pop(sid, None)
            self._smooth_speed.pop(sid, None)

        return result

    def get_speed(self, track_id: int) -> float:
        """Return the latest smoothed speed for a given track ID (km/h)."""
        return self._smooth_speed.get(track_id, 0.0)

    def reset(self):
        self._positions.clear()
        self._smooth_speed.clear()
