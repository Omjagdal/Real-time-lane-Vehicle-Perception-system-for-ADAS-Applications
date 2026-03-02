"""
fcw.py
------
Forward Collision Warning (FCW) module.

Calculates Time-To-Collision (TTC) and emits tiered safety alerts.

Alert Levels:
    SAFE     (TTC ≥ 3.0 s  or distance > 20 m)  → green
    CAUTION  (TTC < 3.0 s  or distance ≤ 20 m)  → yellow
    BRAKE    (TTC < 1.5 s  or distance ≤ 10 m)  → red
"""

import numpy as np
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

TTC_BRAKE    = 1.5   # seconds
TTC_CAUTION  = 3.0   # seconds
DIST_BRAKE   = 10.0  # metres  (critical zone)
DIST_CAUTION = 20.0  # metres  (warning zone)

EGO_SPEED_DEFAULT = 60.0  # km/h — assumed ego-vehicle speed if not provided


# ---------------------------------------------------------------------------
# Alert level
# ---------------------------------------------------------------------------

class AlertLevel(Enum):
    SAFE    = auto()
    CAUTION = auto()
    BRAKE   = auto()

    @property
    def color_bgr(self):
        """OpenCV BGR colour for this alert level."""
        return {
            AlertLevel.SAFE   : (0,   200,  0),
            AlertLevel.CAUTION: (0,   200, 255),
            AlertLevel.BRAKE  : (0,   0,   255),
        }[self]

    @property
    def label(self) -> str:
        return {
            AlertLevel.SAFE   : "✅ SAFE",
            AlertLevel.CAUTION: "⚠️  WARNING",
            AlertLevel.BRAKE  : "🛑 BRAKE!",
        }[self]


# ---------------------------------------------------------------------------
# Warning result container
# ---------------------------------------------------------------------------

@dataclass
class FCWResult:
    track_id   : int
    distance_m : float
    ttc_sec    : Optional[float]   # None when TTC is undefined (closing speed ≤ 0)
    alert      : AlertLevel


# ---------------------------------------------------------------------------
# FCW engine
# ---------------------------------------------------------------------------

class FCWEngine:
    """
    Stateless FCW engine that evaluates collision risk for each tracked vehicle.

    Parameters
    ----------
    ego_speed_kmh : Default ego-vehicle speed (km/h).
                    Pass a live value each call if available (e.g. from OBD).
    """

    def __init__(self, ego_speed_kmh: float = EGO_SPEED_DEFAULT):
        self._ego_speed_default = ego_speed_kmh

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def evaluate(self,
                 tracks,
                 distances : Dict[int, float],
                 speeds    : Dict[int, float],
                 ego_speed : Optional[float] = None) -> Dict[int, FCWResult]:
        """
        Evaluate FCW for all active tracks.

        Parameters
        ----------
        tracks    : List of tracker.Track objects.
        distances : {track_id: distance_m}
        speeds    : {track_id: speed_kmh}
        ego_speed : Ego vehicle speed in km/h (optional).

        Returns
        -------
        dict : {track_id: FCWResult}
        """
        ego_kmh = ego_speed if ego_speed is not None else self._ego_speed_default
        ego_ms  = ego_kmh / 3.6

        results: Dict[int, FCWResult] = {}
        for track in tracks:
            tid     = track.track_id
            dist_m  = distances.get(tid, 999.0)
            veh_kmh = speeds.get(tid, 0.0)
            veh_ms  = veh_kmh / 3.6

            # Relative closing speed (positive = approaching)
            closing_ms = ego_ms - veh_ms
            ttc: Optional[float] = None
            if closing_ms > 0.5:
                ttc = dist_m / closing_ms

            alert = self._classify(dist_m, ttc)

            results[tid] = FCWResult(
                track_id   = tid,
                distance_m = dist_m,
                ttc_sec    = ttc,
                alert      = alert,
            )

        return results

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _classify(dist_m: float, ttc: Optional[float]) -> AlertLevel:
        """Determine alert level from distance and TTC."""
        if dist_m <= DIST_BRAKE or (ttc is not None and ttc < TTC_BRAKE):
            return AlertLevel.BRAKE
        if dist_m <= DIST_CAUTION or (ttc is not None and ttc < TTC_CAUTION):
            return AlertLevel.CAUTION
        return AlertLevel.SAFE

    # ------------------------------------------------------------------
    # Utility: find the most dangerous vehicle ahead
    # ------------------------------------------------------------------

    @staticmethod
    def most_critical(results: Dict[int, 'FCWResult']) -> Optional['FCWResult']:
        """
        Return the FCWResult with the highest alert level (and lowest TTC
        as tie-breaker).  Returns None if *results* is empty.
        """
        if not results:
            return None
        level_order = {AlertLevel.BRAKE: 2, AlertLevel.CAUTION: 1, AlertLevel.SAFE: 0}
        return max(results.values(),
                   key=lambda r: (level_order[r.alert],
                                  -(r.ttc_sec if r.ttc_sec is not None else 9999)))
