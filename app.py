"""
app.py
------
Streamlit web interface for the ADAS pipeline.

Run with:
    streamlit run app.py

Features:
  - Upload a video or enter a webcam index
  - Configure YOLO confidence and ego speed
  - Process video with full ADAS pipeline
  - View annotated output in-browser
  - Download the annotated output video
"""

import os
import sys
import time
import tempfile

import cv2
import numpy as np
import streamlit as st


# ---------------------------------------------------------------------------
# Page config (must be the very first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="ADAS Perception System",
    page_icon="🚗",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Lazy imports (so the page loads without GPU init delay)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading ADAS components…")
def load_pipeline(conf: float, device: str, ego_speed: float):
    from src.preprocessing     import TARGET_HEIGHT
    from src.lane_detection    import LaneDetector
    from src.vehicle_detection import VehicleDetector
    from src.tracker           import IoUTracker
    from src.distance          import DistanceEstimator
    from src.speed             import SpeedEstimator
    from src.fcw               import FCWEngine

    return {
        "lane_detector": LaneDetector(),
        "detector"     : VehicleDetector(conf=conf, device=device),
        "tracker"      : IoUTracker(),
        "dist_est"     : DistanceEstimator(frame_height=TARGET_HEIGHT),
        "speed_est"    : SpeedEstimator(fps=30.0),
        "fcw_engine"   : FCWEngine(ego_speed_kmh=ego_speed),
    }


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _process_frame(frame, pipeline, ego_speed):
    from src.preprocessing  import preprocess_for_lane, preprocess_for_detection, resize_frame
    from src.visualization  import draw_lanes, draw_vehicles, draw_fcw_banner, draw_hud
    from src.fcw            import FCWEngine

    edge_img         = preprocess_for_lane(frame)
    prep_frame       = preprocess_for_detection(frame)

    left_lane, right_lane = pipeline["lane_detector"].detect(
        edge_img,
        frame_height=frame.shape[0],
        frame_width =frame.shape[1],
    )

    detections = pipeline["detector"].detect(prep_frame)
    tracks     = pipeline["tracker"].update(detections)
    distances  = pipeline["dist_est"].estimate_all(tracks)
    speeds     = pipeline["speed_est"].update(tracks, distances)
    fcw_res    = pipeline["fcw_engine"].evaluate(tracks, distances, speeds,
                                                 ego_speed=ego_speed)
    critical   = FCWEngine.most_critical(fcw_res)

    from src.preprocessing import TARGET_WIDTH, TARGET_HEIGHT
    out = resize_frame(frame)
    out = draw_lanes(out, left_lane, right_lane)
    out = draw_vehicles(out, tracks, distances, speeds, fcw_res)
    out = draw_fcw_banner(out, critical)
    out = draw_hud(out, fps=0.0, num_tracks=len(tracks),
                   ego_speed_kmh=ego_speed)
    return out, tracks, distances, speeds, fcw_res


# ---------------------------------------------------------------------------
# Main Streamlit app
# ---------------------------------------------------------------------------

def main():
    # ── Header ──────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        .main-title { font-size: 2.4rem; font-weight: 700; color: #00C8FF; }
        .sub-title  { font-size: 1.1rem; color: #AAA; margin-top: -10px; }
        .metric-card { background: #1E1E2E; border-radius: 10px; padding: 12px;
                        text-align: center; border: 1px solid #333; }
        .alert-brake   { color: #FF4444; font-weight: bold; }
        .alert-caution { color: #FFB300; font-weight: bold; }
        .alert-safe    { color: #44FF88; font-weight: bold; }
    </style>

    <p class="main-title">🚗 ADAS Perception System</p>
    <p class="sub-title">Real-Time Lane &amp; Vehicle Perception for Advanced Driver Assistance</p>
    <hr style="border-color:#333; margin-bottom: 1rem;">
    """, unsafe_allow_html=True)

    # ── Sidebar settings ─────────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️  Settings")
        conf      = st.slider("YOLO Confidence", 0.1, 0.95, 0.4, 0.05)
        ego_speed = st.slider("Ego Speed (km/h)", 0, 200, 60, 5)
        device    = st.selectbox("Inference Device", ["cpu", "cuda", "mps"])
        max_frames = st.slider("Max Frames to Process", 50, 2000, 300, 50,
                               help="Limit processing for large videos")
        show_metrics = st.checkbox("Show per-vehicle metrics", value=True)

        st.markdown("---")
        st.markdown("**Pipeline**")
        st.markdown("""
        1. 🎞️ Preprocess frame  
        2. 🛣️ Lane detection (Hough)  
        3. 🚘 Vehicle detection (YOLOv11n)  
        4. 🆔 IoU tracking  
        5. 📏 Distance estimation  
        6. 🏎️ Speed estimation  
        7. ⚠️ FCW (TTC)  
        8. 🎨 Visualisation  
        """)

    # ── File uploader ─────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "Upload a dashcam / traffic video",
        type=["mp4", "avi", "mov", "mkv"]
    )

    if not uploaded:
        st.info("👆  Upload a video file to begin processing.")
        st.markdown("### 🔑 Algorithm Overview")
        cols = st.columns(4)
        info = [
            ("🛣️ Lane Detection", "Canny edges + Hough Lines + ROI masking with temporal smoothing"),
            ("🚘 Vehicle Detection", "YOLOv11n filtered to car / truck / bus / motorcycle"),
            ("📏 Distance", "Pinhole camera model with perspective correction"),
            ("⚠️ FCW", "TTC < 1.5 s → BRAKE • TTC < 3.0 s → WARNING"),
        ]
        for col, (t, d) in zip(cols, info):
            with col:
                st.markdown(f"**{t}**")
                st.caption(d)
        return

    # ── Processing ─────────────────────────────────────────────────────────
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    out_path = tmp_path.replace(".mp4", "_annotated.mp4")

    pipeline = load_pipeline(conf=conf, device=device, ego_speed=ego_speed)

    cap = cv2.VideoCapture(tmp_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_video    = cap.get(cv2.CAP_PROP_FPS) or 30.0

    # Update speed estimator FPS
    pipeline["speed_est"]._fps = fps_video

    st.markdown(f"**Video info:** {total_frames} frames • {fps_video:.1f} FPS")

    from src.preprocessing import TARGET_WIDTH, TARGET_HEIGHT
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps_video,
                             (TARGET_WIDTH, TARGET_HEIGHT))

    # Progress bar + live frame display
    progress_bar   = st.progress(0, text="Processing…")
    preview_slot   = st.empty()
    metrics_slot   = st.empty()

    frame_idx     = 0
    total_tracks  = 0
    alarm_counts  = {"BRAKE": 0, "CAUTION": 0}
    t_start       = time.perf_counter()
    frames_to_process = min(max_frames, total_frames)

    while frame_idx < frames_to_process:
        ret, frame = cap.read()
        if not ret:
            break

        annotated, tracks, distances, speeds, fcw_res = \
            _process_frame(frame, pipeline, ego_speed)

        writer.write(annotated)
        total_tracks = max(total_tracks, len(tracks))

        from src.fcw import AlertLevel
        for r in fcw_res.values():
            if r.alert == AlertLevel.BRAKE:
                alarm_counts["BRAKE"] += 1
            elif r.alert == AlertLevel.CAUTION:
                alarm_counts["CAUTION"] += 1

        # Live preview (every 5 frames to avoid flicker)
        if frame_idx % 5 == 0:
            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            preview_slot.image(rgb, channels="RGB", use_container_width=True)

        frame_idx += 1
        progress_bar.progress(frame_idx / frames_to_process,
                              text=f"Frame {frame_idx}/{frames_to_process}")

    cap.release()
    writer.release()
    elapsed = time.perf_counter() - t_start

    progress_bar.empty()
    st.success(f"✅ Processed {frame_idx} frames in {elapsed:.1f}s  "
               f"({frame_idx / elapsed:.1f} FPS)")

    # ── Summary metrics ──────────────────────────────────────────────────
    st.markdown("### 📊 Session Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Frames Processed", frame_idx)
    c2.metric("Peak Vehicles",    total_tracks)
    c3.metric("🛑 BRAKE Events",  alarm_counts["BRAKE"])
    c4.metric("⚠️ CAUTION Events", alarm_counts["CAUTION"])

    # ── Download ─────────────────────────────────────────────────────────
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            st.download_button(
                label="⬇️  Download Annotated Video",
                data=f,
                file_name="adas_annotated.mp4",
                mime="video/mp4",
            )

    # Cleanup
    try:
        os.unlink(tmp_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
