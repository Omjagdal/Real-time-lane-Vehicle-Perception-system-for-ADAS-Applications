"""
main.py
-------
ADAS pipeline CLI entry point.

Usage:
    python main.py --input <video> [--output <path>] [--fps 30] [--conf 0.4]

Press 'q' to quit the live preview window.
"""

import argparse
import sys
import time
import cv2

from src.preprocessing     import preprocess_for_lane, preprocess_for_detection, resize_frame, TARGET_WIDTH, TARGET_HEIGHT
from src.lane_detection    import LaneDetector
from src.vehicle_detection import VehicleDetector
from src.tracker           import IoUTracker
from src.distance          import DistanceEstimator
from src.speed             import SpeedEstimator
from src.fcw               import FCWEngine
from src.visualization     import draw_lanes, draw_vehicles, draw_fcw_banner, draw_hud


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Real-Time Lane & Vehicle Perception System for ADAS")
    p.add_argument("--input",  "-i", required=True,
                   help="Path to input video file (or webcam index, e.g. 0)")
    p.add_argument("--output", "-o", default="",
                   help="Path to save annotated output video (optional)")
    p.add_argument("--fps",    type=float, default=30.0,
                   help="Target FPS for processing (default: 30)")
    p.add_argument("--conf",   type=float, default=0.4,
                   help="YOLO confidence threshold (default: 0.4)")
    p.add_argument("--device", default="cpu",
                   help="Inference device: cpu | cuda | mps (default: cpu)")
    p.add_argument("--no-display", action="store_true",
                   help="Disable live preview window")
    p.add_argument("--ego-speed", type=float, default=60.0,
                   help="Ego vehicle speed in km/h (default: 60)")
    return p.parse_args()


# ---------------------------------------------------------------------------
# Pipeline components factory
# ---------------------------------------------------------------------------

def build_pipeline(args):
    print("[ADAS] Initialising pipeline components…")
    lane_detector = LaneDetector()
    detector      = VehicleDetector(conf=args.conf, device=args.device)
    tracker       = IoUTracker()
    dist_est      = DistanceEstimator(frame_height=TARGET_HEIGHT)
    speed_est     = SpeedEstimator(fps=args.fps)
    fcw_engine    = FCWEngine(ego_speed_kmh=args.ego_speed)
    print("[ADAS] All components ready. Starting video loop…\n")
    return lane_detector, detector, tracker, dist_est, speed_est, fcw_engine


# ---------------------------------------------------------------------------
# Per-frame processing
# ---------------------------------------------------------------------------

def process_frame(frame, lane_detector, detector, tracker,
                  dist_est, speed_est, fcw_engine, ego_speed):
    """
    Run the full ADAS pipeline on a single BGR frame.
    Returns the annotated frame.
    """
    h, w = frame.shape[:2]

    # 1. Lane detection
    edge_img   = preprocess_for_lane(frame)
    left_lane, right_lane = lane_detector.detect(edge_img, TARGET_HEIGHT, TARGET_WIDTH)

    # 2. Vehicle detection
    prep_frame  = preprocess_for_detection(frame)
    detections  = detector.detect(prep_frame)

    # 3. Tracking
    tracks = tracker.update(detections)

    # 4. Distance estimation
    distances = dist_est.estimate_all(tracks)

    # 5. Speed estimation
    speeds = speed_est.update(tracks, distances)

    # 6. FCW
    fcw_results = fcw_engine.evaluate(tracks, distances, speeds,
                                      ego_speed=ego_speed)

    # 7. Render
    out = resize_frame(frame)                                     # canonical 1280×720
    out = draw_lanes(out, left_lane, right_lane)
    out = draw_vehicles(out, tracks, distances, speeds, fcw_results)

    from src.fcw import FCWEngine
    critical = FCWEngine.most_critical(fcw_results)
    out = draw_fcw_banner(out, critical)
    out = draw_hud(out, fps=0.0, num_tracks=len(tracks),
                   ego_speed_kmh=ego_speed)   # fps injected below

    return out


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # Open video source
    src = int(args.input) if args.input.isdigit() else args.input
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open video source: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Build output writer if requested
    writer = None
    if args.output:
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(args.output, fourcc, args.fps,
                                 (TARGET_WIDTH, TARGET_HEIGHT))
        print(f"[ADAS] Saving output to: {args.output}")

    lane_detector, detector, tracker, dist_est, speed_est, fcw_engine = \
        build_pipeline(args)

    fps_display = args.fps
    frame_count = 0
    t_start     = time.perf_counter()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ADAS] End of video stream.")
                break

            t0  = time.perf_counter()
            out = process_frame(frame, lane_detector, detector, tracker,
                                dist_est, speed_est, fcw_engine, args.ego_speed)

            # Inject live FPS into HUD
            fps_display = 1.0 / max(time.perf_counter() - t0, 1e-6)
            out = draw_hud(out, fps=fps_display, num_tracks=0,
                           ego_speed_kmh=args.ego_speed)

            if writer:
                writer.write(out)

            if not args.no_display:
                cv2.imshow("ADAS — Real-Time Perception", out)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    print("[ADAS] Quit by user.")
                    break

            frame_count += 1
            if frame_count % 30 == 0:
                elapsed = time.perf_counter() - t_start
                print(f"[ADAS] Frame {frame_count:5d} | "
                      f"FPS {fps_display:5.1f} | "
                      f"Elapsed {elapsed:6.1f}s")

    finally:
        cap.release()
        if writer:
            writer.release()
        cv2.destroyAllWindows()
        print(f"[ADAS] Done. Processed {frame_count} frames.")


if __name__ == "__main__":
    main()
