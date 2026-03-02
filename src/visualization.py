"""
visualization.py
----------------
All OpenCV rendering utilities for the ADAS pipeline.

Draws:
  - Detected lane lines (transparent overlay)
  - Vehicle bounding boxes with ID, class, distance, speed
  - FCW alert banners
  - HUD panel (ego speed, FPS, active alerts)
"""

import cv2
import numpy as np
from typing import Dict, List, Optional

from src.fcw import AlertLevel, FCWResult


# ---------------------------------------------------------------------------
# Colour palette (BGR)
# ---------------------------------------------------------------------------
COLOUR_LANE_LEFT   = (0, 255,   0)     # green
COLOUR_LANE_RIGHT  = (0, 255, 255)     # yellow
COLOUR_LANE_FILL   = (0, 160,   0)     # semi-transparent fill
COLOUR_BOX_DEFAULT = (255, 200,  60)   # orange-ish
COLOUR_BOX_BRAKE   = (0,   0, 255)     # red
COLOUR_BOX_CAUTION = (0, 200, 255)     # yellow-orange
COLOUR_BOX_SAFE    = (0, 200,   0)     # green
COLOUR_TEXT        = (255, 255, 255)
COLOUR_HUD_BG      = (20,  20,  20)
COLOUR_HUD_ACCENT  = (0,  200, 255)

LANE_THICKNESS     = 5
BOX_THICKNESS      = 2
FONT               = cv2.FONT_HERSHEY_DUPLEX
FONT_SMALL         = 0.45
FONT_MED           = 0.60
FONT_LARGE         = 0.90


# ---------------------------------------------------------------------------
# Lane overlay
# ---------------------------------------------------------------------------

def draw_lanes(frame: np.ndarray,
               left_line,
               right_line,
               alpha: float = 0.35) -> np.ndarray:
    """
    Draw lane lines and a semi-transparent filled polygon between them.

    Parameters
    ----------
    frame      : BGR image to draw on.
    left_line  : [(x1,y1,x2,y2)] or None
    right_line : [(x1,y1,x2,y2)] or None
    alpha      : Opacity of the fill polygon.
    """
    overlay = frame.copy()
    h, w = frame.shape[:2]

    # Draw solid lane lines
    if left_line:
        x1, y1, x2, y2 = left_line[0]
        cv2.line(overlay, (x1, y1), (x2, y2), COLOUR_LANE_LEFT,  LANE_THICKNESS)

    if right_line:
        x1, y1, x2, y2 = right_line[0]
        cv2.line(overlay, (x1, y1), (x2, y2), COLOUR_LANE_RIGHT, LANE_THICKNESS)

    # Filled polygon between lanes
    if left_line and right_line:
        lx1, ly1, lx2, ly2 = left_line[0]
        rx1, ry1, rx2, ry2 = right_line[0]
        pts = np.array([[lx1, ly1], [lx2, ly2],
                        [rx2, ry2], [rx1, ry1]], dtype=np.int32)
        cv2.fillPoly(overlay, [pts], COLOUR_LANE_FILL)

    return cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)


# ---------------------------------------------------------------------------
# Vehicle boxes
# ---------------------------------------------------------------------------

def draw_vehicles(frame: np.ndarray,
                  tracks,
                  distances : Dict[int, float],
                  speeds    : Dict[int, float],
                  fcw_results: Dict[int, FCWResult]) -> np.ndarray:
    """Draw bounding boxes + info labels for each tracked vehicle."""
    for track in tracks:
        tid   = track.track_id
        x1, y1, x2, y2 = track.bbox
        dist  = distances.get(tid)
        speed = speeds.get(tid)
        fcw   = fcw_results.get(tid)

        # Box colour by alert level
        if fcw is not None:
            colour = {
                AlertLevel.BRAKE  : COLOUR_BOX_BRAKE,
                AlertLevel.CAUTION: COLOUR_BOX_CAUTION,
                AlertLevel.SAFE   : COLOUR_BOX_SAFE,
            }.get(fcw.alert, COLOUR_BOX_DEFAULT)
        else:
            colour = COLOUR_BOX_DEFAULT

        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, BOX_THICKNESS)

        # Top label: ID + class
        label = f"#{tid} {track.label}"
        _put_label(frame, label, (x1, y1 - 2), colour, FONT_SMALL)

        # Bottom label: distance + speed
        metrics = []
        if dist is not None:
            metrics.append(f"{dist:.1f} m")
        if speed is not None:
            metrics.append(f"{speed:.0f} km/h")
        if metrics:
            _put_label(frame, "  ".join(metrics), (x1, y2 + 14), colour, FONT_SMALL)

    return frame


# ---------------------------------------------------------------------------
# FCW alert banner
# ---------------------------------------------------------------------------

def draw_fcw_banner(frame: np.ndarray,
                    critical: Optional[FCWResult]) -> np.ndarray:
    """Draw a full-width alert banner at the bottom of the frame if braking."""
    if critical is None or critical.alert == AlertLevel.SAFE:
        return frame

    h, w = frame.shape[:2]
    banner_h = 50

    overlay = frame.copy()
    colour  = critical.alert.color_bgr
    cv2.rectangle(overlay, (0, h - banner_h), (w, h), colour, -1)
    frame = cv2.addWeighted(overlay, 0.75, frame, 0.25, 0)

    ttc_text = (f"  TTC: {critical.ttc_sec:.1f}s" if critical.ttc_sec else "")
    text = (f"{critical.alert.label}  |  "
            f"Dist: {critical.distance_m:.1f} m{ttc_text}")
    cv2.putText(frame, text,
                (10, h - 15),
                FONT, FONT_MED, COLOUR_TEXT, 2, cv2.LINE_AA)
    return frame


# ---------------------------------------------------------------------------
# HUD panel
# ---------------------------------------------------------------------------

def draw_hud(frame: np.ndarray,
             fps          : float,
             num_tracks   : int,
             ego_speed_kmh: float = 0.0) -> np.ndarray:
    """Draw a semi-transparent HUD in the top-left corner."""
    panel_w = 220
    panel_h = 90
    margin  = 10

    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (margin, margin),
                  (margin + panel_w, margin + panel_h),
                  COLOUR_HUD_BG, -1)
    frame = cv2.addWeighted(overlay, 0.65, frame, 0.35, 0)

    lines = [
        f"FPS        : {fps:.1f}",
        f"Vehicles   : {num_tracks}",
        f"Ego speed  : {ego_speed_kmh:.0f} km/h",
    ]
    for i, text in enumerate(lines):
        y = margin + 20 + i * 22
        cv2.putText(frame, text,
                    (margin + 8, y),
                    FONT, FONT_SMALL, COLOUR_HUD_ACCENT, 1, cv2.LINE_AA)

    # "ADAS ACTIVE" badge (top-right)
    _, fw = frame.shape[:2]
    badge = "⬛ ADAS ACTIVE"
    (bw, bh), _ = cv2.getTextSize(badge, FONT, FONT_SMALL, 1)
    bx = frame.shape[1] - bw - margin * 2
    by = margin + 18
    cv2.putText(frame, badge, (bx, by),
                FONT, FONT_SMALL, (0, 255, 180), 1, cv2.LINE_AA)

    return frame


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _put_label(frame: np.ndarray,
               text  : str,
               origin: tuple,
               colour: tuple,
               scale : float):
    """Draw a text string with a dark drop-shadow for legibility."""
    x, y = origin
    # Shadow
    cv2.putText(frame, text, (x + 1, y + 1),
                FONT, scale, (0, 0, 0), 2, cv2.LINE_AA)
    # Main text
    cv2.putText(frame, text, (x, y),
                FONT, scale, colour, 1, cv2.LINE_AA)
