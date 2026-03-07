"""
app.py
------
Streamlit web interface for the ADAS pipeline.

Run with:
    streamlit run app.py

Features:
  - Upload a dashcam / traffic video
  - Configure YOLO confidence, ego speed, and device
  - Full ADAS pipeline with live preview
  - Annotated video download + session summary
"""

import os
import time
import tempfile

import cv2
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
# Pipeline loader (cached — only re-created when settings change)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="⚙️  Loading ADAS pipeline…")
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
# Per-frame ADAS processing
# ---------------------------------------------------------------------------

def _process_frame(frame, pipeline, ego_speed, fps_live=0.0):
    from src.preprocessing import preprocess_for_lane, preprocess_for_detection, resize_frame
    from src.visualization import draw_lanes, draw_vehicles, draw_fcw_banner, draw_hud
    from src.fcw           import FCWEngine

    edge_img  = preprocess_for_lane(frame)
    prep_frame = preprocess_for_detection(frame)

    left_lane, right_lane = pipeline["lane_detector"].detect(
        edge_img,
        frame_height=frame.shape[0],
        frame_width =frame.shape[1],
    )

    detections = pipeline["detector"].detect(prep_frame)
    tracks     = pipeline["tracker"].update(detections)
    distances  = pipeline["dist_est"].estimate_all(tracks)
    speeds     = pipeline["speed_est"].update(tracks, distances)
    fcw_res    = pipeline["fcw_engine"].evaluate(
        tracks, distances, speeds, ego_speed=ego_speed)
    critical   = FCWEngine.most_critical(fcw_res)

    out = resize_frame(frame)
    out = draw_lanes(out, left_lane, right_lane)
    out = draw_vehicles(out, tracks, distances, speeds, fcw_res)
    out = draw_fcw_banner(out, critical)
    out = draw_hud(out, fps=fps_live, num_tracks=len(tracks),
                   ego_speed_kmh=ego_speed)
    return out, tracks, fcw_res


# ---------------------------------------------------------------------------
# Streamlit image helper — Streamlit ≥1.42 renamed use_container_width
# ---------------------------------------------------------------------------

def _st_image(slot, img_rgb):
    """Display image across full column width — handles API version changes."""
    try:
        slot.image(img_rgb, channels="RGB", width="stretch")
    except TypeError:
        # Older Streamlit fallback
        slot.image(img_rgb, channels="RGB", use_container_width=True)


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] { background: #0E1117; }
        .adas-title { font-size: 2.4rem; font-weight: 800;
                      background: linear-gradient(90deg, #00C8FF, #0066FF);
                      -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .adas-sub   { font-size: 1.05rem; color: #888; margin-top: -8px; }
    </style>
    <p class="adas-title">🚗 ADAS Perception System</p>
    <p class="adas-sub">Real-Time Lane &amp; Vehicle Perception · YOLOv11n · IoU Tracking · FCW</p>
    <hr style="border-color:#2a2a2a; margin: 0.5rem 0 1.2rem 0;">
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        conf       = st.slider("YOLO Confidence", 0.1, 0.95, 0.40, 0.05)
        ego_speed  = st.slider("Ego Speed (km/h)", 0, 200, 60, 5)
        device     = st.selectbox("Inference Device", ["cpu", "cuda", "mps"])
        max_frames = st.slider("Max Frames", 50, 3000, 500, 50,
                               help="Cap how many frames are processed")

        st.markdown("---")
        st.markdown("**📐 Pipeline Steps**")
        st.markdown("""
1. 🎞️ Pre-process (resize + Canny)  
2. 🛣️ Lane detection (Hough Lines)  
3. 🚘 Vehicle detection (YOLOv11n)  
4. 🆔 IoU multi-object tracking  
5. 📏 Distance estimation (pinhole)  
6. 🏎️ Speed estimation (EMA)  
7. ⚠️ Forward Collision Warning (TTC)  
8. 🎨 Visualisation overlay  
""")
        st.markdown("---")
        st.caption("FCW thresholds · BRAKE < 1.5 s · CAUTION < 3.0 s")

    # ── Upload ────────────────────────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📁  Upload a dashcam or traffic camera video",
        type=["mp4", "avi", "mov", "mkv"],
        help="MP4 recommended. Large files may take a while on CPU.",
    )

    if not uploaded:
        # Landing-page info cards
        st.info("👆  Upload a video above to start the ADAS pipeline.")
        c1, c2, c3, c4 = st.columns(4)
        cards = [
            ("🛣️ Lane Detection",   "Canny edges + Hough Lines + temporal smoothing"),
            ("🚘 Vehicle Detection", "YOLOv11n filtered to car / truck / bus / motorcycle"),
            ("📏 Distance",          "Pinhole camera model with perspective correction"),
            ("⚠️ FCW",               "TTC < 1.5 s → 🛑 BRAKE  |  TTC < 3.0 s → ⚠️ CAUTION"),
        ]
        for col, (title, desc) in zip([c1, c2, c3, c4], cards):
            with col:
                st.markdown(f"**{title}**")
                st.caption(desc)
        return

    # ── Save upload to disk & open with OpenCV ────────────────────────────────
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name

    out_path = tmp_path.replace(".mp4", "_adas.mp4")

    # ── Load pipeline ─────────────────────────────────────────────────────────
    pipeline = load_pipeline(conf=conf, device=device, ego_speed=ego_speed)

    cap          = cv2.VideoCapture(tmp_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_video    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    pipeline["speed_est"]._fps = fps_video

    vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    st.markdown(f"""
    **Video info:**  {total_frames} frames · {fps_video:.1f} FPS · {vid_w}×{vid_h}
    """)

    from src.preprocessing import TARGET_WIDTH, TARGET_HEIGHT
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps_video,
                             (TARGET_WIDTH, TARGET_HEIGHT))

    # ── Processing UI ─────────────────────────────────────────────────────────
    col_preview, col_stats = st.columns([3, 1])

    with col_preview:
        st.markdown("**Live Preview**")
        preview_slot = st.empty()

    with col_stats:
        st.markdown("**Live Stats**")
        fps_slot    = st.empty()
        track_slot  = st.empty()
        brake_slot  = st.empty()
        caution_slot = st.empty()

    progress_bar = st.progress(0, text="Starting…")

    # Processing loop
    frame_idx       = 0
    total_tracks_max = 0
    alarm_counts    = {"BRAKE": 0, "CAUTION": 0}
    t_start         = time.perf_counter()
    frames_to_proc  = min(max_frames, total_frames)

    from src.fcw import AlertLevel

    while frame_idx < frames_to_proc:
        ret, frame = cap.read()
        if not ret:
            break

        t0 = time.perf_counter()

        annotated, tracks, fcw_res = _process_frame(
            frame, pipeline, ego_speed,
            fps_live=round(1.0 / max(time.perf_counter() - t0, 0.001), 1)
        )

        fps_live = round(1.0 / max(time.perf_counter() - t0, 0.001), 1)
        writer.write(annotated)

        for r in fcw_res.values():
            if r.alert == AlertLevel.BRAKE:
                alarm_counts["BRAKE"] += 1
            elif r.alert == AlertLevel.CAUTION:
                alarm_counts["CAUTION"] += 1
        total_tracks_max = max(total_tracks_max, len(tracks))

        # Live preview every 8 frames
        if frame_idx % 8 == 0:
            rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
            _st_image(preview_slot, rgb)

            # Stats panel
            fps_slot.metric("⚡ FPS", fps_live)
            track_slot.metric("🚘 Vehicles", len(tracks))
            brake_slot.metric("🛑 BRAKE events", alarm_counts["BRAKE"])
            caution_slot.metric("⚠️ CAUTION events", alarm_counts["CAUTION"])

        frame_idx += 1
        progress_bar.progress(
            frame_idx / frames_to_proc,
            text=f"Frame {frame_idx} / {frames_to_proc}"
        )

    cap.release()
    writer.release()
    elapsed = time.perf_counter() - t_start
    progress_bar.empty()

    # ── Completion ────────────────────────────────────────────────────────────
    st.success(
        f"✅ Done! Processed **{frame_idx} frames** in **{elapsed:.1f}s** "
        f"({frame_idx / max(elapsed, 0.01):.1f} FPS average)"
    )

    # Summary metrics
    st.markdown("### 📊 Session Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Frames Processed",  frame_idx)
    m2.metric("Peak Vehicles",     total_tracks_max)
    m3.metric("🛑 BRAKE Events",   alarm_counts["BRAKE"])
    m4.metric("⚠️ CAUTION Events", alarm_counts["CAUTION"])

    # Download button
    if os.path.exists(out_path):
        with open(out_path, "rb") as f:
            st.download_button(
                label="⬇️  Download Annotated Video",
                data=f,
                file_name="adas_annotated.mp4",
                mime="video/mp4",
                use_container_width=True,
            )

    # Cleanup temp input
    try:
        os.unlink(tmp_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
